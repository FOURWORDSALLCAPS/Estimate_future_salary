import requests
import time
from terminaltables import AsciiTable
from collections import defaultdict
from environs import Env


def predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if salary and salary['currency'] == 'RUR':
        if salary['from'] and salary['to']:
            expected_salary = (salary['from'] + salary['to']) / 2
            return int(expected_salary)
        elif salary['from']:
            expected_salary = salary['from'] * 1.2
            return int(expected_salary)
        else:
            expected_salary = salary['to'] * 0.8
            return int(expected_salary)
    else:
        return None


def predict_rub_salary_sj(vacancy):
    if vacancy['payment_from'] and vacancy['payment_to']:
        expected_salary = (vacancy['payment_from'] + vacancy['payment_to']) / 2
        return int(expected_salary)
    elif vacancy['payment_from']:
        expected_salary = vacancy['payment_from'] * 1.2
        return int(expected_salary)
    elif vacancy['payment_to']:
        expected_salary = vacancy['payment_to'] * 0.8
        return int(expected_salary)
    else:
        return None


def get_statistics_hh(languages):
    url_hh = "https://api.hh.ru/vacancies"
    salaries_hh = defaultdict(lambda: {"vacancies_found": 0, "vacancies_processed": 0, "average_salary": 0})
    headers_hh = {
        'User-Agent': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
        'Referer': 'https://hh.ru/search/vacancy'
    }
    table_data_hh = [
        ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    ]
    title_hh = 'HeadHunter Moscow'
    for language in languages:
        params = {"text": language, "area": 1, "only_with_salary": True, "period": 30}
        response = requests.get(url_hh, params=params, headers=headers_hh)
        response.raise_for_status()
        if response.ok:
            pages = response.json()["pages"]
            found = response.json()["found"]
            salaries_hh[language]["vacancies_found"] = found
            vacancies_processed = 0
            average_salary = 0
            for page in range(pages):
                params = {"text": language, "area": 1, "only_with_salary": True, "page": page}
                response = requests.get(url_hh, params=params, headers=headers_hh)
                response.raise_for_status()
                time.sleep(1)
                if response.ok:
                    vacancies = response.json()["items"]
                    for vacancy in vacancies:
                        expected_salary = predict_rub_salary_hh(vacancy)
                        if expected_salary:
                            vacancies_processed += 1
                            average_salary += expected_salary
            if vacancies_processed > 0:
                salaries_hh[language]["average_salary"] = int(average_salary / vacancies_processed)
            salaries_hh[language]["vacancies_processed"] = vacancies_processed
        salary = salaries_hh[language]
        table_row = [
            language,
            salary['vacancies_found'],
            salary['vacancies_processed'],
            salary['average_salary']
        ]
        table_data_hh.append(table_row)
    table_hh = AsciiTable(table_data_hh, title_hh)
    return table_hh.table


def get_statistics_sj(languages, api_key):
    url_sj = 'https://api.superjob.ru/2.33/vacancies/'
    salaries_sj = defaultdict(lambda: {"vacancies_found": 0, "vacancies_processed": 0, "average_salary": 0})
    headers_sj = {'X-Api-App-Id': f'{api_key}'}
    table_data_sj = [
        ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    ]
    title_sj = 'SuperJob Moscow'
    for language in languages:
        page = 0
        pages = 1
        vacancies_processed = 0
        salary_sum = 0
        while page < pages:
            page += 1
            params = {
                'keyword': language,
                'town': 4,
                'catalogues': 48,
                'count': page
            }
            response = requests.get(url_sj, headers=headers_sj, params=params)
            response.raise_for_status()
            time.sleep(0.5)
            result = response.json()
            vacancies = result['objects']
            if not vacancies:
                break
            pages = result['total'] // len(vacancies) + 1
            for vacancy in vacancies:
                vacancies_processed += 1
                salary = predict_rub_salary_sj(vacancy)
                if salary:
                    salaries_sj[language]['average_salary'] += salary
                    salary_sum += salary
            salaries_sj[language]['vacancies_found'] = result['total']
            salaries_sj[language]['vacancies_processed'] = vacancies_processed
        for keyword, salary in salaries_sj.items():
            vacancies_processed = salary['vacancies_processed']
            if vacancies_processed > 0:
                salaries_sj[keyword]['average_salary'] = int(salary['average_salary'] / vacancies_processed)
        salary = salaries_sj[language]
        table_row = [
            language,
            salary['vacancies_found'],
            salary['vacancies_processed'],
            salary['average_salary']
        ]
        table_data_sj.append(table_row)
    table_sh = AsciiTable(table_data_sj, title_sj)
    return table_sh.table


def main():
    env = Env()
    env.read_env()
    api_key = env("HH_API_KEY")
    languages = ["Python", "Java", "JavaScript", "PHP", "C#", "Swift", "Objective-C", "Ruby", "Scala", "Go"]
    print(get_statistics_hh(languages))
    print(get_statistics_sj(languages, api_key))


if __name__ == "__main__":
    main()
