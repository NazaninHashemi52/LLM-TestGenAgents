"""String utilities module — a simple stateless CUT used as a baseline."""


def _check_str(*values):
    """Raise TypeError if any value is not a str."""
    for v in values:
        if not isinstance(v, str):
            raise TypeError(f"Expected str, got {type(v).__name__!r}")


def reverse(s):
    """Return s reversed."""
    _check_str(s)
    return s[::-1]


def is_palindrome(s, ignore_case=True, ignore_spaces=True):
    """Return True if s reads the same forwards and backwards.

    By default, letter case and whitespace are ignored. The empty string is
    considered a palindrome.
    """
    _check_str(s)
    if ignore_spaces:
        s = "".join(s.split())
    if ignore_case:
        s = s.lower()
    return s == s[::-1]


def count_vowels(s):
    """Return the number of vowels (a, e, i, o, u — case-insensitive) in s."""
    _check_str(s)
    return sum(1 for ch in s.lower() if ch in "aeiou")


def capitalize_words(s):
    """Capitalize the first letter of every whitespace-separated word.

    Runs of whitespace are collapsed into a single space and leading/trailing
    whitespace is removed.
    """
    _check_str(s)
    return " ".join(word[0].upper() + word[1:] for word in s.split())


def truncate(s, max_length, suffix="..."):
    """Shorten s to at most max_length characters, ending with suffix.

    If s already fits, it is returned unchanged.

    Raises:
        ValueError: if max_length is negative or shorter than suffix.
    """
    _check_str(s, suffix)
    if not isinstance(max_length, int) or isinstance(max_length, bool):
        raise TypeError("max_length must be an int")
    if max_length < 0:
        raise ValueError("max_length must be non-negative")
    if len(s) <= max_length:
        return s
    if max_length < len(suffix):
        raise ValueError("max_length is shorter than the suffix")
    return s[: max_length - len(suffix)] + suffix


def word_frequencies(s):
    """Return a dict mapping each lower-cased word to its number of occurrences.

    Leading and trailing punctuation (.,!?;:) is stripped from each word; words
    that become empty are ignored.
    """
    _check_str(s)
    freqs = {}
    for raw in s.split():
        word = raw.strip(".,!?;:").lower()
        if not word:
            continue
        freqs[word] = freqs.get(word, 0) + 1
    return freqs


def to_snake_case(s):
    """Convert a CamelCase, kebab-case or space separated string to snake_case.

    Examples: "HelloWorld" -> "hello_world", "my-var name" -> "my_var_name".
    """
    _check_str(s)
    out = []
    for i, ch in enumerate(s):
        if ch in " -":
            out.append("_")
        elif ch.isupper():
            if i > 0 and out and out[-1] != "_" and not s[i - 1].isupper():
                out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch)
    # Collapse repeated underscores and trim them from the ends
    result = "".join(out)
    while "__" in result:
        result = result.replace("__", "_")
    return result.strip("_")


def caesar_cipher(s, shift):
    """Shift each ASCII letter in s by `shift` positions, wrapping around.

    Case is preserved; non-letters are left unchanged. Negative shifts decode.
    """
    _check_str(s)
    if not isinstance(shift, int) or isinstance(shift, bool):
        raise TypeError("shift must be an int")
    result = []
    for ch in s:
        if "a" <= ch <= "z":
            result.append(chr((ord(ch) - ord("a") + shift) % 26 + ord("a")))
        elif "A" <= ch <= "Z":
            result.append(chr((ord(ch) - ord("A") + shift) % 26 + ord("A")))
        else:
            result.append(ch)
    return "".join(result)
