/*
 * WtHftStraDemo.h  — WonderTrader HFT Strategy (Translated to English)
 * ======================================================================
 * Original: Chinese comments translated by platform init
 * Architecture: Tick-driven micro-price-imbalance arbitrage
 *               feeds signal into exchange-core matching engine
 */
#pragma once
#include <unordered_set>
#include <memory>
#include <thread>
#include <mutex>

#include "../Includes/HftStrategyDefs.h"

class WtHftStraDemo : public HftStrategy
{
public:
	WtHftStraDemo(const char* id);
	~WtHftStraDemo();

private:
	// Cancel stale orders that exceed the time threshold
	void check_orders();

	// Core signal computation and order routing
	void do_calc(IHftStraCtx* ctx);

public:
	virtual const char* getName() override;

	virtual const char* getFactName() override;

	// Load config parameters: code, second, freq, offset, reserve, stock
	virtual bool init(WTSVariant* cfg) override;

	// Initialize: subscribe to tick feed, load 30x 1-min bars as warm-up
	virtual void on_init(IHftStraCtx* ctx) override;

	// Primary event: new tick arrives — run signal logic or check open orders
	virtual void on_tick(IHftStraCtx* ctx, const char* code, WTSTickData* newTick) override;

	// Bar close event (unused in tick-driven HFT, reserved for bar-level logic)
	virtual void on_bar(IHftStraCtx* ctx, const char* code, const char* period,
	                    uint32_t times, WTSBarStruct* newBar) override;

	// Trade fill confirmed: re-run signal immediately
	virtual void on_trade(IHftStraCtx* ctx, uint32_t localid, const char* stdCode,
	                      bool isBuy, double qty, double price,
	                      const char* userTag) override;

	// Position update (reserved for portfolio-level risk checks)
	virtual void on_position(IHftStraCtx* ctx, const char* stdCode, bool isLong,
	                         double prevol, double preavail,
	                         double newvol, double newavail) override;

	// Order status update: clean up filled/cancelled order IDs, re-run signal
	virtual void on_order(IHftStraCtx* ctx, uint32_t localid, const char* stdCode,
	                      bool isBuy, double totalQty, double leftQty,
	                      double price, bool isCanceled,
	                      const char* userTag) override;

	// Channel connected: cancel any untracked open orders, set ready flag
	virtual void on_channel_ready(IHftStraCtx* ctx) override;

	// Channel disconnected: halt all new signals
	virtual void on_channel_lost(IHftStraCtx* ctx) override;

	// Order acknowledgement callback
	virtual void on_entrust(uint32_t localid, bool bSuccess,
	                        const char* message, const char* userTag) override;

private:
	WTSTickData*    _last_tick;        // Last received tick data
	IHftStraCtx*    _ctx;              // Strategy execution context
	std::string     _code;             // Instrument code (e.g. "AAPL" or "SSE.600000")
	uint32_t        _secs;             // Order expiry threshold in seconds
	uint32_t        _freq;             // Minimum recompute interval in seconds
	int32_t         _offset;           // Price tick offset for order placement
	uint32_t        _unit;             // Order unit size (1 for futures, 100 for stocks)
	double          _reserved;         // Base/reserved position (not traded against)
	bool            _stock;            // True = stock mode (unit=100), False = futures

	typedef std::unordered_set<uint32_t> IDSet;
	IDSet           _orders;           // Active local order IDs being tracked
	std::mutex      _mtx_ords;         // Mutex protecting _orders set

	uint64_t        _last_entry_time;  // Timestamp of last order entry (nanoseconds)
	bool            _channel_ready;    // True when broker channel is connected
	uint32_t        _last_calc_time;   // Last minute bar when spread was recalculated
	uint32_t        _cancel_cnt;       // Running count of cancellations (risk circuit)
};
