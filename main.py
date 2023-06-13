import requests
import time
from collections import defaultdict


def predict_rub_salary(vacancy):
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


def main():
    url = "https://api.hh.ru/vacancies"
    languages = ["Python", "Java", "JavaScript", "PHP", "C#", "Swift", "Objective-C", "Ruby", "Scala", "Go"]
    salaries = defaultdict(lambda: {"vacancies_found": 0, "vacancies_processed": 0, "average_salary": 0})
    headers = {
        'User-Agent': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
        'Referer': 'https://hh.ru/search/vacancy'
    }
    for language in languages:
        params = {"text": language, "area": 1, "only_with_salary": True, "period": 30}
        response = requests.get(url, params=params, headers=headers)
        if response.ok:
            pages = response.json()["pages"]
            found = response.json()["found"]
            salaries[language]["vacancies_found"] = found
            vacancies_processed = 0
            average_salary = 0
            for page in range(pages):
                params = {"text": language, "area": 1, "only_with_salary": True, "page": page}
                response = requests.get(url, params=params, headers=headers)
                time.sleep(1)
                if response.ok:
                    vacancies = response.json()["items"]
                    for vacancy in vacancies:
                        expected_salary = predict_rub_salary(vacancy)
                        if expected_salary:
                            vacancies_processed += 1
                            average_salary += expected_salary
            if vacancies_processed > 0:
                salaries[language]["average_salary"] = int(average_salary / vacancies_processed)
            salaries[language]["vacancies_processed"] = vacancies_processed
    print(salaries)


if __name__ == "__main__":
    main()
