import re


def fmt(s: str) -> str:
	return re.sub(r"[\s\n\t\r]*", "", s) if type(s) is str else ""
