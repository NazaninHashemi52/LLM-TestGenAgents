"""Bank account module — a class-based CUT with custom exceptions and edge cases."""


class BankError(Exception):
    """Base exception for all banking errors."""


class InsufficientFundsError(BankError):
    """Raised when a withdrawal or transfer exceeds the available balance."""


class AccountFrozenError(BankError):
    """Raised when an operation is attempted on a frozen account."""


class InvalidAmountError(BankError, ValueError):
    """Raised when an amount is not a positive finite number."""


def _validate_amount(amount):
    """Return amount if it is a positive int/float, otherwise raise."""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TypeError(f"amount must be numeric, got {type(amount).__name__!r}")
    if amount != amount or amount in (float("inf"), float("-inf")):
        raise InvalidAmountError("amount must be finite")
    if amount <= 0:
        raise InvalidAmountError("amount must be positive")
    return amount


class BankAccount:
    """A bank account with an optional overdraft limit and a daily withdrawal limit.

    Amounts are stored rounded to 2 decimal places.
    """

    DEFAULT_DAILY_LIMIT = 1000.0

    def __init__(self, owner, balance=0.0, overdraft_limit=0.0,
                 daily_limit=DEFAULT_DAILY_LIMIT):
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("owner must be a non-empty string")
        if isinstance(balance, bool) or not isinstance(balance, (int, float)):
            raise TypeError("balance must be numeric")
        if balance < 0:
            raise InvalidAmountError("initial balance cannot be negative")
        if overdraft_limit < 0:
            raise InvalidAmountError("overdraft_limit cannot be negative")
        if daily_limit <= 0:
            raise InvalidAmountError("daily_limit must be positive")

        self.owner = owner.strip()
        self._balance = round(float(balance), 2)
        self._overdraft_limit = float(overdraft_limit)
        self._daily_limit = float(daily_limit)
        self._withdrawn_today = 0.0
        self._frozen = False
        self._transactions = []  # list of (kind, amount, balance_after)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def balance(self):
        """Current balance (may be negative when using an overdraft)."""
        return self._balance

    @property
    def available(self):
        """Amount that can still be withdrawn, respecting overdraft and daily limit."""
        by_balance = self._balance + self._overdraft_limit
        by_daily = self._daily_limit - self._withdrawn_today
        return round(max(0.0, min(by_balance, by_daily)), 2)

    @property
    def is_frozen(self):
        return self._frozen

    @property
    def transactions(self):
        """Return a copy of the transaction log."""
        return list(self._transactions)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_active(self):
        if self._frozen:
            raise AccountFrozenError(f"account of {self.owner} is frozen")

    def _log(self, kind, amount):
        self._transactions.append((kind, amount, self._balance))

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def deposit(self, amount):
        """Deposit a positive amount and return the new balance."""
        self._ensure_active()
        amount = _validate_amount(amount)
        self._balance = round(self._balance + amount, 2)
        self._log("deposit", amount)
        return self._balance

    def withdraw(self, amount):
        """Withdraw a positive amount and return the new balance.

        Raises:
            AccountFrozenError: if the account is frozen.
            InsufficientFundsError: if amount exceeds balance + overdraft.
            BankError: if amount exceeds the remaining daily limit.
        """
        self._ensure_active()
        amount = _validate_amount(amount)
        if amount > self._balance + self._overdraft_limit:
            raise InsufficientFundsError(
                f"cannot withdraw {amount}: balance {self._balance}, "
                f"overdraft {self._overdraft_limit}"
            )
        if self._withdrawn_today + amount > self._daily_limit:
            raise BankError("daily withdrawal limit exceeded")
        self._balance = round(self._balance - amount, 2)
        self._withdrawn_today += amount
        self._log("withdraw", amount)
        return self._balance

    def transfer(self, other, amount):
        """Move amount from this account to other.

        Both accounts are checked before any money moves, so a failed
        transfer leaves both balances unchanged.
        """
        if not isinstance(other, BankAccount):
            raise TypeError("can only transfer to another BankAccount")
        if other is self:
            raise BankError("cannot transfer to the same account")
        other._ensure_active()
        self.withdraw(amount)
        other.deposit(amount)
        self._transactions[-1] = ("transfer_out", amount, self._balance)
        other._transactions[-1] = ("transfer_in", amount, other._balance)

    def apply_interest(self, annual_rate, months=1):
        """Apply monthly-compounded interest to a positive balance.

        Negative balances are charged at the same rate. Returns the interest
        amount (negative if charged).
        """
        self._ensure_active()
        if not 0 <= annual_rate <= 1:
            raise InvalidAmountError("annual_rate must be between 0 and 1")
        if not isinstance(months, int) or months < 1:
            raise InvalidAmountError("months must be a positive int")
        if self._balance == 0:
            return 0.0
        factor = (1 + annual_rate / 12) ** months
        new_balance = round(self._balance * factor, 2)
        interest = round(new_balance - self._balance, 2)
        self._balance = new_balance
        self._log("interest", interest)
        return interest

    def reset_daily_limit(self):
        """Reset the amount withdrawn today (called at the start of a new day)."""
        self._withdrawn_today = 0.0

    def freeze(self):
        self._frozen = True

    def unfreeze(self):
        self._frozen = False

    def statement(self):
        """Return a multi-line human-readable statement."""
        lines = [f"Statement for {self.owner}"]
        for kind, amount, balance_after in self._transactions:
            lines.append(f"{kind:<13}{amount:>10.2f}{balance_after:>12.2f}")
        lines.append(f"{'balance':<13}{'':>10}{self._balance:>12.2f}")
        return "\n".join(lines)
