import requests
import time
from terminaltables import AsciiTable
from environs import Env


def calculate_expected_salary(salary_from, salary_to):
    if salary_from and salary_to:
        expected_salary = (salary_from + salary_to) / 2
        return int(expected_salary)
    elif salary_from:
        expected_salary = salary_from * 1.2
        return int(expected_salary)
    else:
        expected_salary = salary_to * 0.8
        return int(expected_salary)


def predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if salary and salary['currency'] == 'RUR':
        expected_salary = calculate_expected_salary(salary['from'], salary['to'])
        return expected_salary


def predict_rub_salary_sj(vacancy):
    if vacancy:
        expected_salary = calculate_expected_salary(vacancy['payment_from'], vacancy['payment_to'])
        return expected_salary


def get_statistics_hh(languages):
    url_hh = "https://api.hh.ru/vacancies"
    headers_hh = {
        'User-Agent': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
        'Referer': 'https://hh.ru/search/vacancy'
    }
    salaries_hh = {}
    for language in languages:
        moscow_region = 1
        month = 30
        params = {"text": language, "area": moscow_region, "only_with_salary": True, "period": month}
        response = requests.get(url_hh, params=params, headers=headers_hh)
        response.raise_for_status()
        if not response.ok:
            continue
        server_response = response.json()
        pages = server_response["pages"]
        found = server_response["found"]
        vacancies_processed = 0
        average_salary = 0
        for page in range(pages):
            params = {"page": page}
            response = requests.get(url_hh, params=params, headers=headers_hh)
            response.raise_for_status()
            time.sleep(0.5)
            if not response.ok:
                continue
            vacancies = response.json()["items"]
            for vacancy in vacancies:
                expected_salary = predict_rub_salary_hh(vacancy)
                if not expected_salary:
                    continue
                vacancies_processed += 1
                average_salary += expected_salary
        if vacancies_processed > 0:
            average_salary = int(average_salary / vacancies_processed)
            vacancies_found = found
        else:
            average_salary = 0
            vacancies_found = 0
        salary = {"vacancies_found": vacancies_found,
                  "vacancies_processed": vacancies_processed,
                  "average_salary": average_salary}
        salaries_hh[language] = salary
    return salaries_hh


def get_statistics_sj(languages, api_key):
    url_sj = 'https://api.superjob.ru/2.33/vacancies/'
    headers_sj = {'X-Api-App-Id': f'{api_key}'}
    salaries_sj = {}
    for language in languages:
        page = 0
        pages = 1
        vacancies_processed = 0
        average_salary = 0
        found = 0
        moscow = 4
        programmers = 48
        average_salary_sj = 0
        while page < pages:
            page += 1
            params = {
                'keyword': language,
                'town': moscow,
                'catalogues': programmers,
                'count': page
            }
            response = requests.get(url_sj, headers=headers_sj, params=params)
            response.raise_for_status()
            time.sleep(0.5)
            server_response = response.json()
            found = server_response['total']
            vacancies = server_response['objects']
            if not vacancies:
                break
            pages = server_response['total'] // len(vacancies) + 1
            for vacancy in vacancies:
                expected_salary = predict_rub_salary_sj(vacancy)
                if expected_salary:
                    vacancies_processed += 1
                    average_salary += expected_salary
        if vacancies_processed:
            average_salary_sj = int(average_salary / vacancies_processed)
        salary = {"vacancies_found": found,
                  "vacancies_processed": vacancies_processed,
                  "average_salary": average_salary_sj}
        salaries_sj[language] = salary
    return salaries_sj


def create_chart(statistics, title):
    chart = [
        ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    ]
    for language, salary in statistics.items():
        table_row = [
            language,
            salary['vacancies_found'],
            salary['vacancies_processed'],
            salary['average_salary']
        ]
        chart.append(table_row)
    table = AsciiTable(chart, title)
    return table.table


def main():
    env = Env()
    env.read_env()
    api_key = env("SJ_API_KEY")
    languages = ["Python", "Java", "JavaScript", "PHP", "C#", "Swift", "Objective-C", "Ruby", "Scala", "Go"]
    title_sj = 'SuperJob Moscow'
    title_hh = 'HeadHunter Moscow'
    statistics_sj = get_statistics_sj(languages, api_key)
    statistics_hh = get_statistics_hh(languages)
    print(create_chart(statistics_hh, title_hh))
    print(create_chart(statistics_sj, title_sj))


if __name__ == "__main__":
    main()
