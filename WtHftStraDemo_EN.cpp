/*
 * WtHftStraDemo.cpp — WonderTrader HFT Micro-Price Imbalance Strategy
 * =====================================================================
 * Translated from Chinese. All logic preserved exactly.
 * Chinese comment translations inline.
 *
 * SIGNAL: Micro-price (volume-weighted mid) vs last price
 *   theoretical_price = (bid_price * ask_qty + ask_price * bid_qty)
 *                       / (ask_qty + bid_qty)
 *
 *   theoretical > last → BUY  signal (positive imbalance)
 *   theoretical < last → SELL signal (negative imbalance)
 *
 * EXECUTION:
 *   BUY  → place limit at (last + offset * tick_size)
 *   SELL → place limit at (last - offset * tick_size)
 *   Cancel if order age > _secs seconds (anti-adverse-selection)
 *
 * INTEGRATION with exchange-core:
 *   Signal output → ExecutionBridge → ExchangeCore.submitOrder()
 */

#include "WtHftStraDemo_EN.h"
#include "../Includes/IHftStraCtx.h"
#include "../Includes/WTSVariant.hpp"
#include "../Includes/WTSDataDef.hpp"
#include "../Includes/WTSContractInfo.hpp"
#include "../Share/TimeUtils.hpp"
#include "../Share/decimal.h"
#include "../Share/fmtlib.h"

extern const char* FACT_NAME;

WtHftStraDemo::WtHftStraDemo(const char* id)
    : HftStrategy(id)
    , _last_tick(NULL)
    , _last_entry_time(UINT64_MAX)
    , _channel_ready(false)
    , _last_calc_time(0)
    , _stock(false)
    , _unit(1)
    , _cancel_cnt(0)
    , _reserved(0)
{}

WtHftStraDemo::~WtHftStraDemo()
{
    if (_last_tick)
        _last_tick->release();
}

const char* WtHftStraDemo::getName()   { return "HftDemoStrategy"; }
const char* WtHftStraDemo::getFactName() { return FACT_NAME; }

bool WtHftStraDemo::init(WTSVariant* cfg)
{
    // Demonstration of reading externally-passed parameters
    _code     = cfg->getCString("code");
    _secs     = cfg->getUInt32("second");
    _freq     = cfg->getUInt32("freq");
    _offset   = cfg->getUInt32("offset");
    _reserved = cfg->getDouble("reserve");

    _stock = cfg->getBoolean("stock");
    _unit  = _stock ? 100 : 1;   // Stocks trade in lots of 100

    return true;
}

void WtHftStraDemo::on_entrust(uint32_t localid, bool bSuccess,
                                const char* message, const char* userTag)
{
    // Order acknowledgement — extend here for order tracking / logging
}

void WtHftStraDemo::on_init(IHftStraCtx* ctx)
{
    // Warm-up: request last 30 x 1-minute bars (for spread baseline if needed)
    WTSKlineSlice* kline = ctx->stra_get_bars(_code.c_str(), "m1", 30);
    if (kline)
        kline->release();

    // Subscribe to tick feed for this instrument
    ctx->stra_sub_ticks(_code.c_str());

    _ctx = ctx;
}

void WtHftStraDemo::do_calc(IHftStraCtx* ctx)
{
    const char* code = _code.c_str();

    // Do not recompute within the same frequency window (avoids over-trading)
    uint64_t now = TimeUtils::makeTime(
        ctx->stra_get_date(),
        ctx->stra_get_time() * 100000 + ctx->stra_get_secs()
    );
    if (now - _last_entry_time <= _freq * 1000)
        return;

    WTSTickData* curTick = ctx->stra_get_last_tick(code);
    if (curTick == NULL)
        return;

    // actiontime is in millisecond format; divide by 100000 to extract the minute
    uint32_t curMin = curTick->actiontime() / 100000;
    if (curMin > _last_calc_time)
    {
        // If spread was computed in a prior minute, update the last-compute timestamp
        _last_calc_time = curMin;
    }

    // ── SIGNAL COMPUTATION ──────────────────────────────────────────────────
    int32_t signal = 0;
    double price = curTick->price();

    // Theoretical (micro) price = volume-weighted average of best bid and ask
    // This is the true "fair value" given current order book imbalance
    double micro_price = (
        curTick->bidprice(0) * curTick->askqty(0) +
        curTick->askprice(0) * curTick->bidqty(0)
    ) / (curTick->bidqty(0) + curTick->askqty(0));

    if      (micro_price > price) signal =  1;   // Positive signal: fair value above last → BUY
    else if (micro_price < price) signal = -1;   // Negative signal: fair value below last → SELL

    // ── ORDER ROUTING ───────────────────────────────────────────────────────
    if (signal != 0)
    {
        double curPos = ctx->stra_get_position(code);
        curPos -= _reserved;   // Exclude reserved/base position from signal decision

        WTSCommodityInfo* cInfo = ctx->stra_get_comminfo(code);

        if (signal > 0 && curPos <= 0)
        {
            // Positive signal and flat/short → Enter long
            // Place limit order offset ticks above last price (aggressive entry)
            double targetPx = price + cInfo->getPriceTick() * _offset;
            auto ids = ctx->stra_buy(code, targetPx, _unit, "enterlong");

            _mtx_ords.lock();
            for (auto localid : ids) _orders.insert(localid);
            _mtx_ords.unlock();
            _last_entry_time = now;
        }
        else if (signal < 0 && (curPos > 0 ||
                 ((!_stock || !decimal::eq(_reserved, 0)) && curPos == 0)))
        {
            // Negative signal and long/flat → Enter short
            // (For stocks: only short if reserved position allows it)
            // Place limit order offset ticks below last price
            double targetPx = price - cInfo->getPriceTick() * _offset;
            auto ids = ctx->stra_sell(code, targetPx, _unit, "entershort");

            _mtx_ords.lock();
            for (auto localid : ids) _orders.insert(localid);
            _mtx_ords.unlock();
            _last_entry_time = now;
        }
    }

    curTick->release();
}

void WtHftStraDemo::on_tick(IHftStraCtx* ctx, const char* code, WTSTickData* newTick)
{
    if (_code.compare(code) != 0)
        return;

    // If we have open orders, prioritize checking their status first
    if (!_orders.empty())
    {
        check_orders();
        return;
    }

    if (!_channel_ready)
        return;

    do_calc(ctx);
}

void WtHftStraDemo::check_orders()
{
    if (!_orders.empty() && _last_entry_time != UINT64_MAX)
    {
        uint64_t now = TimeUtils::makeTime(
            _ctx->stra_get_date(),
            _ctx->stra_get_time() * 100000 + _ctx->stra_get_secs()
        );
        // If order has been open longer than the expiry threshold → cancel
        // (anti-adverse-selection: stale limit orders are poisoned)
        if (now - _last_entry_time >= _secs * 1000)
        {
            _mtx_ords.lock();
            for (auto localid : _orders)
            {
                _ctx->stra_cancel(localid);
                _cancel_cnt++;
                _ctx->stra_log_info(
                    fmt::format("Order expired, cancel count updated to {}",
                                _cancel_cnt).c_str()
                );
            }
            _mtx_ords.unlock();
        }
    }
}

void WtHftStraDemo::on_bar(IHftStraCtx* ctx, const char* code, const char* period,
                            uint32_t times, WTSBarStruct* newBar)
{
    // Reserved for bar-level strategy extensions
}

void WtHftStraDemo::on_trade(IHftStraCtx* ctx, uint32_t localid, const char* stdCode,
                              bool isBuy, double qty, double price, const char* userTag)
{
    // Trade confirmed → immediately re-evaluate signal
    do_calc(ctx);
}

void WtHftStraDemo::on_position(IHftStraCtx* ctx, const char* stdCode, bool isLong,
                                 double prevol, double preavail,
                                 double newvol, double newavail)
{
    // Reserved for portfolio-level position risk integration
}

void WtHftStraDemo::on_order(IHftStraCtx* ctx, uint32_t localid, const char* stdCode,
                              bool isBuy, double totalQty, double leftQty,
                              double price, bool isCanceled, const char* userTag)
{
    // Only process orders we submitted
    auto it = _orders.find(localid);
    if (it == _orders.end())
        return;

    // If the order is fully cancelled or fully filled → remove from tracking
    if (isCanceled || leftQty == 0)
    {
        _mtx_ords.lock();
        _orders.erase(it);
        if (_cancel_cnt > 0)
        {
            _cancel_cnt--;
            _ctx->stra_log_info(
                fmt::format("Cancel count → {}", _cancel_cnt).c_str()
            );
        }
        _mtx_ords.unlock();

        // Re-run signal after order resolution
        do_calc(ctx);
    }
}

void WtHftStraDemo::on_channel_ready(IHftStraCtx* ctx)
{
    // Check for any open orders that are NOT in our tracking set
    double undone = _ctx->stra_get_undone(_code.c_str());
    if (!decimal::eq(undone, 0) && _orders.empty())
    {
        // Untracked open orders found → cancel all for safety
        _ctx->stra_log_info(
            fmt::format("{} has {} untracked open orders — cancelling all",
                        _code, undone).c_str()
        );

        bool isBuy  = (undone > 0);
        OrderIDs ids = _ctx->stra_cancel(_code.c_str(), isBuy, undone);
        for (auto localid : ids)
        {
            _orders.insert(localid);
        }
        _cancel_cnt += ids.size();

        _ctx->stra_log_info(
            fmt::format("Cancel count → {}", _cancel_cnt).c_str()
        );
    }

    _channel_ready = true;
}

void WtHftStraDemo::on_channel_lost(IHftStraCtx* ctx)
{
    // Channel disconnected → halt all signal generation
    _channel_ready = false;
}
