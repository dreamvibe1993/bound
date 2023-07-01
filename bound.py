import argparse
import os
import re
from re import Match
from typing import Union

mobx_reserved_words: "list[str]" = ['observable', 'action.bound', 'computed']


# Process strings

def get_class_name(ts_class: str) -> str:
	class_name = re.search(r"(?<=class\s)\w+", ts_class)
	return class_name.group(0) if class_name else ts_class


def create_bounds(actions: "list[str]") -> "list[str]":
	list_of_actions_bound: list[str] = []
	for action in actions:
		list_of_actions_bound.append(f"{action}: action.bound")
	return sorted(list_of_actions_bound)


def create_observables(observables: "list[str]") -> "list[str]":
	list_of_observables: list[str] = []
	for observable in observables:
		list_of_observables.append(f"{observable}: observable")
	return sorted(list_of_observables)


def create_computeds(computeds: "list[str]") -> "list[str]":
	list_of_computeds: list[str] = []
	for computed in computeds:
		list_of_computeds.append(f"{computed}: computed")
	return sorted(list_of_computeds)


def create_mobx_observables_js_object(ts_class) -> str:
	class_name = get_class_name(ts_class)
	variables: list[str] = get_all_observables_in_class(ts_class)
	actions: list[str] = get_all_actions_in_class(ts_class)
	getters_setters: list[str] = get_all_computeds_in_class(ts_class)
	observables_str: str = ""
	actions_bound_str: str = ""
	computeds_str = ""
	if len(variables) > 0:
		observables = ',\n'.join(f'    {o}' for o in create_observables(variables))
		observables_str = f"\n{observables},\n"
	if len(getters_setters) > 0:
		computeds = ',\n'.join(f'    {c}' for c in create_computeds(getters_setters))
		computeds_str = f"\n{computeds},\n"
	if len(actions) > 0:
		actions_bound = ',\n'.join(f'    {a}' for a in create_bounds(actions))
		actions_bound_str = f'\n{actions_bound},\n'
	obj = f'export const {class_name[0].lower() + class_name[1:]}Observables = {{{observables_str}{computeds_str}{actions_bound_str}}};'
	return obj


def get_all_observables_in_class(ts_class: str) -> "list[str]":
	def cut_all_before_constructor(ts_class_string: str) -> str:
		cut = re.search(r"(?<={)[^%]*(?=constructor)", ts_class_string)
		return cut.group(0) if cut else ts_class_string

	def get_rid_of_comments(piece: str) -> str:
		return re.sub(r"/.*?\*/", "", piece, flags=re.DOTALL)

	def cut_everything_after_eq_sign(piece: str) -> str:
		return re.sub(r"\s=.+?;", ";", piece, flags=re.DOTALL)

	def cut_everything_after_ddot(piece: str) -> str:
		return re.sub(r":.+?(?=;)", "", piece, flags=re.DOTALL)

	def cut_reserved_words(piece: str) -> str:
		observables: list[str] = piece.split(";")
		observables_processed: list[str] = []
		for observable in observables:
			if "abstract" in observable: continue
			observable_processed = re.sub(r"\w+(?=\s)", "", observable)
			observables_processed.append(observable_processed.strip())
		all_observables_to_string = re.sub(r"(\n*|\s*)", "", ";".join(observables_processed).strip())
		return all_observables_to_string

	ts_class_copy = ts_class
	ts_class_copy: str = cut_all_before_constructor(ts_class_copy)
	ts_class_copy: str = get_rid_of_comments(ts_class_copy)
	ts_class_copy: str = cut_everything_after_eq_sign(ts_class_copy)
	ts_class_copy: str = cut_everything_after_ddot(ts_class_copy)
	ts_class_copy: str = cut_reserved_words(ts_class_copy)
	observables: list[str] = []
	for observable in ts_class_copy.split(";"):
		if observable != "" and observable not in observables:
			observables.append(re.sub(r"\W*", "", observable))
	return sorted(observables)


def get_all_actions_in_class(ts_class: str) -> "list[str]":
	observables = get_all_observables_in_class(ts_class)
	ts_class_copy = ts_class
	for observable in observables:
		ts_class_copy = re.sub(fr"(?<=\s\s)(private|abstract|protected)?\s{observable}.*", "", ts_class_copy)
	ts_class_copy = re.sub(r"^.*class\s.+{", "", ts_class_copy, re.DOTALL).strip()
	ts_class_copy = re.sub(r"constructor[^}]*}", "", ts_class_copy, re.DOTALL)
	ts_class_copy = re.sub(r"async\s", "", ts_class_copy, re.DOTALL)
	ts_class_copy = re.sub(r"(get|set)\s[^}]*}", "", ts_class_copy, re.DOTALL)
	ts_class_copy = re.sub(r"(?<=\)):[^}]*?(?={)", "", ts_class_copy, re.DOTALL)
	ts_class_copy = re.sub(r"\(.*?\)", "()", ts_class_copy, flags=re.DOTALL)
	ts_class_copy = re.sub(r":[^%\n]+?{", "()", ts_class_copy, re.DOTALL)
	dirty_methods: list[str] = re.findall(r"(?<!\w\s)(?<=\s)\w+\(\)[^;),]{?\n?", ts_class_copy,
	                                      flags=re.DOTALL | re.MULTILINE)
	methods: list[str] = []
	for d_method in dirty_methods:
		methods.append(re.sub(r"[(){\n\r\s]", "", d_method))
	print(methods)
	return sorted(methods)


def get_all_computeds_in_class(ts_class: str) -> "list[str]":
	computeds: list[str] = re.findall(r"(?<=get\s)\w+", ts_class) + re.findall(r"(?<=set\s)\w+", ts_class)
	return sorted(computeds)


def get_class_model(ts_file: str) -> str:
	class_model = re.search(r"(export\s)?class\s[A-Z]\w+[^%]*}", ts_file)
	return class_model.group(0) if class_model else ts_file


def get_existing_mobx_observables_obj(model_str: str) -> str:
	if 'Observables' not in model_str:
		print('Кажется, в этом файле нет объекта, оканчивающегося на Observables. Вы правильно назвали объект?')
	observables_js_obj: Union[Match[bytes], None, Match[str]] = re.search(
		r"(export\s)?const\s\w+(Observables)\s=\s{[^/]*?};",
		model_str)
	if not observables_js_obj: return ""
	string_found = observables_js_obj.group(0)
	is_real_mobx_obj: bool = False
	for r_word in mobx_reserved_words:
		if is_real_mobx_obj: break
		is_real_mobx_obj = r_word in string_found
	if not is_real_mobx_obj: return ""
	return string_found


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
	description='Синхронизация mobx observables моделей')
parser.add_argument('path', help='Путь к директории или файлу TS.')

args = parser.parse_args()
path: str = args.path

if os.path.isfile(path) and path.endswith('.ts'):
	process_file(path)
else:
	print(
		f"Указанный путь '{path}' не является файлом TS.")
