import re


def fmt(s: str) -> str:
	return re.sub(r"[\s\n\t\r]*", "", s)
