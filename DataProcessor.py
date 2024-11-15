from init import PointsConfig
from datetime import datetime,timedelta
import re


class DataProcessor:
    def __init__(self, data: list[dict[str, str | None]]):
        self.data = data
        self.points = PointsConfig()

    def filter_by_city(self, data: list[dict[str, str | None]], city_name: str) -> list[dict[str, str | None]]:
        if city_name == "Вся Україна (віддалено)":
            return data
        return [item for item in data if item.get('Місто:') == city_name]

    def filter_old_resumes(self,data, days_threshold=21):
        """відфільтруємо старі резюме, гадаю більше 3ох тижнів неактуальні """
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        filtered_resumes = [
            r for r in data if datetime.strptime(r['resume_time'], '%Y-%m-%d %H:%M:%S') > threshold_date
        ]
        return filtered_resumes

    def filter_by_salary(self, data: list[dict[str, str | None]], max_salary: str) -> list[dict[str, str | None]]:
        filtered_data = []
        for item in data:
            salary = item.get('salary')
            if salary:
                try:
                    numeric_salary = int(salary)
                    if numeric_salary <= int(max_salary):
                        filtered_data.append(item)
                except ValueError:
                    # Якщо зарплата не є числом, пропускаємо
                    continue
            else:
                # Якщо зарплата не вказана, додаємо до результату
                filtered_data.append(item)
        return filtered_data

    def apply_filters(self, city_name: str = None, max_salary: str = None) -> list[dict[str, str | None]]:
        filtered_data = self.data

        if city_name is not None:
            filtered_data = self.filter_by_city(filtered_data, city_name)

        if max_salary is not None:
            filtered_data = self.filter_by_salary(filtered_data, max_salary)

        filtered_data = self.filter_old_resumes(filtered_data)

        return filtered_data

    def __skillsCount(self, resume: dict[str, str | None]) -> int:
        return len(resume['skills']) * self.points.skill

    def __daysDifferenPoint(self, resume: dict[str, str | None]) -> int:
        resume_time = datetime.strptime(resume['resume_time'], '%Y-%m-%d %H:%M:%S')
        today = datetime.now()
        days_difference = (today - resume_time).days
        if days_difference <= 1:
            return self.points.date_resume.points["d<=1"]
        elif 1 < days_difference <= 7:
            return self.points.date_resume.points["1<d<=7"]
        elif 7 < days_difference <= 14:
            return self.points.date_resume.points["7<d<14"]
        elif 14 < days_difference:
            return 0

    def __englishLevelPoints(self, resume: dict[str, str | None]) -> int:
        for lang in resume.get('languages', []):
            if 'Англійська' in lang:
                level = lang.split('—')[-1].strip()
                if level == 'середній':
                    return self.points.language.levels["середній"]
                elif level == 'вище середнього':
                    return self.points.language.levels["вище середнього"]
                elif level == 'просунутий':
                    return self.points.language.levels["просунутий"]
                elif level == 'вільно':
                    return self.points.language.levels["вільно"]

        return 0

    def __skillsMatchesPoints(self, skills_str: str, resume: dict[str, str | None]) -> int:
        skills = resume['skills']
        skills_lower = {skill.lower() for skill in skills}

        # Розділяємо рядок required_skills і також приводимо до нижнього регістру
        required_skills_list = {skill.strip().lower() for skill in skills_str.split(",")}

        # Знаходимо збіги між множинами
        matches = skills_lower & required_skills_list

        return round(len(matches) * self.points.skill_match)

    def __experiencePoint(self, resume: dict[str, str | None]) -> int:
        total_months = 0

        # Регулярні вирази для пошуку кількості років і місяців
        years_pattern = re.compile(r'(\d+)\s*р(ік|оки|оків)')
        months_pattern = re.compile(r'(\d+)\s*місяц(ь|і|ів)')
        experience = resume['experience']

        for item in experience:
            duration = item.get('duration', '')

            years = 0
            months = 0

            years_match = years_pattern.search(duration)
            if years_match:
                years = int(years_match.group(1))

            months_match = months_pattern.search(duration)
            if months_match:
                months = int(months_match.group(1))

            total_months += years * 12 + months
        return round(total_months * self.points.experience_month)

    def pointsDetermination(self, skills: str, filtered_data: list[dict[str, str | None]]) -> list[
        dict[str, str | None]]:

        for resume in filtered_data:
            print(resume)
            resume['points'] = self.__skillsCount(resume)
            resume['points'] += self.__daysDifferenPoint(resume)
            resume['points'] += self.__englishLevelPoints(resume)
            resume['points'] += self.__skillsMatchesPoints(skills, resume)
            resume['points'] += self.__experiencePoint(resume)


        sorted_data = sorted(filtered_data, key=lambda x: x['points'], reverse=True)

        return sorted_data


# --------------------------деякі функції-----------------------------------
# Функція для обробки навичок
def format_skills(skills: list[str]) -> str:
    if not skills:
        return "не вказано"
    return " | ".join(skills)


# Функція для обробки зарплати
def format_salary(salary: str | None) -> str:
    return "не вказано" if salary is None else salary
