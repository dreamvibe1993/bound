import argparse
import os
import re
from re import Match
from typing import Union


def get_all_observables_in_class(ts_class: str) -> "list[str]":
	def cut_all_before_constructor(ts_class_string: str) -> str:
		cut = re.search(r"(?<={)[^%]*(?=constructor)", ts_class_string)
		return cut.group(0) if cut else ""

	def get_rid_of_comments(piece: str) -> str:
		return re.sub(r"/.*?\*/", "", piece, flags=re.DOTALL)

	def cut_everything_after_eq_sign(piece: str) -> str:
		return re.sub(r"\s=.+?;", ";", piece, flags=re.DOTALL)

	def cut_everything_after_ddot(piece: str) -> str:
		return re.sub(r":.+?(?=;)", "", piece, flags=re.DOTALL)

	def cut_reserved_words(piece: str) -> str:
		obsers: list[str] = piece.split(";")
		observables_processed: list[str] = []
		for obser in obsers:
			observables_processed.append(re.sub(r"\w(?=\s)", "", obser))
		return re.sub(r"(\n*|\s*)", "", ";".join(observables_processed).strip())

	piece_b4_constructor: str = cut_all_before_constructor(ts_class)
	no_comments: str = get_rid_of_comments(piece_b4_constructor)
	equalized: str = cut_everything_after_eq_sign(no_comments)
	no_types: str = cut_everything_after_ddot(equalized)
	no_res_words: str = cut_reserved_words(no_types)
	observables: list[str] = []
	for observable in no_res_words.split(";"):
		if observable != "":
			observables.append(re.sub(r"\W*", "", observable))
	return observables


def get_class_model(ts_file: str) -> str:
	class_model: Union[Match[bytes], None, Match[str]] = re.search(r"(export\s)?class\s[A-Z]\w+[^%]*}", ts_file)
	return class_model.group(0) if class_model else ""


def get_existing_mobx_observables_obj(model_str: str) -> str:
	observables_js_obj: Union[Match[bytes], None, Match[str]] = re.search(r"(export\s)?const\s\w+\s=\s{[^/]*};",
	                                                                      model_str)
	return observables_js_obj.group(0) if observables_js_obj else ""


# Read and handle data
def parse_file(file_path: str) -> str:
	try:
		with open(file_path, 'r') as file:
			return file.read()
	except FileNotFoundError:
		print(f"Ошибка: Файл '{file_path}' не найден.")
	except Exception as e:
		print(f"Произошла ошибка при обработке файла '{file_path}': {str(e)}")


def process_file(file_path):
	try:
		ts_file = parse_file(file_path)
		if ts_file is not None:
			print("Working...", ts_file)
	except Exception as e:
		print(f"Произошла ошибка при обработке файла '{file_path}': {str(e)}")


parser = argparse.ArgumentParser(
	description='Надо дописать')
parser.add_argument('path', help='Путь к директории или файлу TSX/TS.')

args = parser.parse_args()
path: str = args.path

if os.path.isfile(path) and path.endswith('.ts'):
	process_file(path)
else:
	print(
		f"Указанный путь '{path}' не является файлом TS.")
