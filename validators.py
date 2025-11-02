"""
Input validation utilities for Quant Trading project
Ensures safe and valid user inputs
"""

import re
from datetime import datetime, timedelta
import pandas as pd


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_ticker(ticker):
    """
    Validate stock ticker symbol

    Args:
        ticker (str): Stock ticker symbol

    Returns:
        str: Validated and normalized ticker (uppercase)

    Raises:
        ValidationError: If ticker format is invalid
    """
    if not ticker:
        raise ValidationError("티커 심볼을 입력해주세요")

    ticker = ticker.strip().upper()

    # Basic ticker format validation (1-5 uppercase letters)
    if not re.match(r'^[A-Z]{1,10}$', ticker):
        raise ValidationError(
            f"잘못된 티커 형식: {ticker}. "
            "티커는 1-10자의 영문자만 포함해야 합니다 (예: AAPL, NVDA)"
        )

    return ticker


def validate_date(date_str, date_name="날짜"):
    """
    Validate date string in YYYY-MM-DD format

    Args:
        date_str (str): Date string
        date_name (str): Name of the date field for error messages

    Returns:
        str: Validated date string

    Raises:
        ValidationError: If date format is invalid
    """
    if not date_str:
        raise ValidationError(f"{date_name}를 입력해주세요")

    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')

        # Check if date is not in the future
        if parsed_date > datetime.now():
            raise ValidationError(f"{date_name}는 미래 날짜일 수 없습니다")

        # Check if date is not too old (e.g., before 1980)
        if parsed_date.year < 1980:
            raise ValidationError(f"{date_name}는 1980년 이후여야 합니다")

        return date_str

    except ValueError:
        raise ValidationError(
            f"잘못된 날짜 형식: {date_str}. "
            "YYYY-MM-DD 형식으로 입력해주세요 (예: 2020-01-01)"
        )


def validate_date_range(start_date, end_date):
    """
    Validate that start_date is before end_date

    Args:
        start_date (str): Start date string
        end_date (str): End date string

    Raises:
        ValidationError: If date range is invalid
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    if start >= end:
        raise ValidationError("시작 날짜는 종료 날짜보다 이전이어야 합니다")

    # Check if date range is reasonable (at least 7 days)
    if (end - start).days < 7:
        raise ValidationError("날짜 범위는 최소 7일 이상이어야 합니다")

    # Check if date range is not too long (e.g., max 20 years)
    if (end - start).days > 365 * 20:
        raise ValidationError("날짜 범위는 최대 20년까지만 가능합니다")


def validate_moving_average_period(period, min_val=1, max_val=500):
    """
    Validate moving average period

    Args:
        period (int or str): Moving average period
        min_val (int): Minimum allowed value
        max_val (int): Maximum allowed value

    Returns:
        int: Validated period

    Raises:
        ValidationError: If period is invalid
    """
    try:
        period = int(period)
    except (ValueError, TypeError):
        raise ValidationError(f"이동평균 기간은 정수여야 합니다: {period}")

    if period < min_val or period > max_val:
        raise ValidationError(
            f"이동평균 기간은 {min_val}에서 {max_val} 사이여야 합니다. "
            f"입력값: {period}"
        )

    return period


def validate_ma_pair(ma1, ma2):
    """
    Validate that short MA is less than long MA

    Args:
        ma1 (int): Short moving average period
        ma2 (int): Long moving average period

    Raises:
        ValidationError: If MA pair is invalid
    """
    if ma1 >= ma2:
        raise ValidationError(
            f"짧은 이동평균(ma1={ma1})은 긴 이동평균(ma2={ma2})보다 작아야 합니다"
        )


def validate_positive_number(value, name="값", min_val=0.0001):
    """
    Validate that a number is positive

    Args:
        value (float or str): Value to validate
        name (str): Name of the value for error messages
        min_val (float): Minimum allowed value

    Returns:
        float: Validated value

    Raises:
        ValidationError: If value is invalid
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name}는 숫자여야 합니다: {value}")

    if value < min_val:
        raise ValidationError(f"{name}는 {min_val} 이상이어야 합니다. 입력값: {value}")

    return value


def validate_percentage(value, name="비율", min_val=0, max_val=100):
    """
    Validate percentage value

    Args:
        value (float or str): Percentage value
        name (str): Name of the value
        min_val (float): Minimum percentage
        max_val (float): Maximum percentage

    Returns:
        float: Validated percentage

    Raises:
        ValidationError: If percentage is invalid
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name}는 숫자여야 합니다: {value}")

    if value < min_val or value > max_val:
        raise ValidationError(
            f"{name}는 {min_val}%에서 {max_val}% 사이여야 합니다. "
            f"입력값: {value}%"
        )

    return value


def validate_dataframe(df, required_columns=None):
    """
    Validate pandas DataFrame

    Args:
        df (pd.DataFrame): DataFrame to validate
        required_columns (list): List of required column names

    Raises:
        ValidationError: If DataFrame is invalid
    """
    if df is None:
        raise ValidationError("데이터프레임이 None입니다")

    if not isinstance(df, pd.DataFrame):
        raise ValidationError("입력은 pandas DataFrame이어야 합니다")

    if df.empty:
        raise ValidationError("데이터프레임이 비어있습니다")

    if required_columns:
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValidationError(
                f"필수 컬럼이 없습니다: {', '.join(missing_cols)}"
            )


def get_validated_input(prompt, validator_func, *args, **kwargs):
    """
    Get validated input from user with retry logic

    Args:
        prompt (str): Input prompt
        validator_func (callable): Validation function
        *args, **kwargs: Arguments to pass to validator_func

    Returns:
        Validated input value

    Example:
        ticker = get_validated_input('티커: ', validate_ticker)
        ma1 = get_validated_input('MA1: ', validate_moving_average_period)
    """
    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        try:
            user_input = input(prompt)
            validated_value = validator_func(user_input, *args, **kwargs)
            return validated_value

        except ValidationError as e:
            attempts += 1
            remaining = max_attempts - attempts

            if remaining > 0:
                print(f"❌ 오류: {e}")
                print(f"남은 시도 횟수: {remaining}\n")
            else:
                print(f"❌ 오류: {e}")
                raise ValidationError(
                    f"최대 시도 횟수({max_attempts})를 초과했습니다"
                )

        except KeyboardInterrupt:
            print("\n입력이 취소되었습니다")
            raise


# Convenience functions for common validations
def get_ticker():
    """Get validated ticker from user input"""
    return get_validated_input('티커 심볼 (예: AAPL): ', validate_ticker)


def get_date(prompt="날짜 (YYYY-MM-DD): "):
    """Get validated date from user input"""
    return get_validated_input(prompt, validate_date)


def get_ma_period(prompt, min_val=1, max_val=500):
    """Get validated moving average period from user input"""
    return get_validated_input(
        prompt,
        validate_moving_average_period,
        min_val=min_val,
        max_val=max_val
    )


# Example usage
if __name__ == '__main__':
    print("=== 입력 검증 테스트 ===\n")

    try:
        # Test ticker validation
        print("✓ 올바른 티커:", validate_ticker('AAPL'))
        print("✓ 올바른 티커:", validate_ticker(' nvda '))  # Should normalize

        # Test date validation
        print("✓ 올바른 날짜:", validate_date('2020-01-01'))

        # Test MA validation
        print("✓ 올바른 MA:", validate_moving_average_period(10))

        # Test invalid inputs
        print("\n잘못된 입력 테스트:")
        try:
            validate_ticker('INVALID123')
        except ValidationError as e:
            print(f"✓ 티커 검증 실패 (예상됨): {e}")

        try:
            validate_moving_average_period(-5)
        except ValidationError as e:
            print(f"✓ MA 검증 실패 (예상됨): {e}")

        print("\n모든 검증 테스트 통과!")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
