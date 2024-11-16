import re
import httpx
from bs4 import BeautifulSoup
from init import logger

class WorkUaParser:
    """Клас для парсингу резюме з сайту Work.ua"""

    def __init__(self, position: str, experience: str):
        self.position: str = position
        self.base_url: str = f'https://www.work.ua/resumes-{self.__corectPosition(position)}/'
        self.experience: str = experience

    def __corectPosition(self, position:str)->str:
        """ коригуємо символи для коректного пошуку C#, C++ програмістів"""
        return position.replace(" ", "-").replace("#","%23").replace("++","%2B%2B")

    def __fetch_html(self, url: str) -> str | None:
        """Завантажує HTML-сторінку за заданим URL."""
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except httpx.RequestError as e:
            logger.error(f"Помилка під час запиту: {e}")
            return None

    def __experience_to_parameter(self, experience: str) -> str:
        """формує параметер досвіду"""
        experience_mapping = {
            "Без досвіду": "experience=0",
            "До 1 року": "experience=1",
            "Від 1 до 2 років": "experience=164",
            "Від 2 до 5 років": "experience=165",
            "Понад 5 років": "experience=166",
            "Усі варіанти": "experience=0+1+164+165+166",
        }
        return experience_mapping.get(experience, "")

    def __parse_resume_link(self, resume) -> str:
        """Отримує посилання на резюме та витягує його ID."""
        resume_link = resume.find('a')['href']
        resume_id = re.search(r'\d+', resume_link).group()
        return f"https://www.work.ua/resumes/{resume_id}/"

    def __parse_salary_and_position(self, resume_card) -> dict[str, str | None]:
        """Витягує посаду та зарплату з резюме."""
        position_salary = resume_card.find("h2").text.strip()
        result = {"position": None, "salary": None}

        if match := re.search(r'(\d[\d\s]*)\s?грн', position_salary):
            result['salary'] = match.group(1).strip().replace(" ", "").replace("\xa0", "")
            result['position'] = position_salary.replace(match.group(0), "").strip()
        else:
            result['position'] = position_salary

        return result

    def __parse_personal_info(self, resume_card) -> dict[str, str]:
        """Витягує особисті дані, такі як вік, місце проживання та інше."""
        container = resume_card.find("dl", class_="dl-horizontal")
        personal_info = {}
        for dt_tag in container.find_all("dt"):
            field_name = dt_tag.get_text(strip=True)
            dd_tag = dt_tag.find_next_sibling("dd")
            if dd_tag:
                if field_name == "Місто проживання:":
                    field_name = "Місто:"
                personal_info[field_name] = dd_tag.get_text(strip=True)
        return personal_info

    def __parse_languages(self, resume_card) -> list[str]:
        """Витягує список мов із резюме."""
        languages_section = resume_card.find('h2', string='Знання мов')
        if not languages_section:
            return []

        languages_list = languages_section.find_next('ul')
        return [li.get_text(strip=True) for li in languages_list.find_all('li')]

    def __parse_experience(self, resume_card) -> list[dict[str, str]]:
        """Витягує інформацію про досвід роботи з резюме."""
        experience_section = resume_card.find('h2', string='Досвід роботи')
        if not experience_section:
            return []

        job_experiences = []
        for h2 in experience_section.find_all_next(['h2'], class_=True):
            job_title = h2.get_text(strip=True)
            if p_tag := h2.find_next('p'):
                time_period = p_tag.find('span', class_='text-default-7')
                if time_period:
                    duration = time_period.get_text(strip=True).replace("\xa0", " ").replace("(", "").replace(")", "")
                    job_experiences.append({"title": job_title, "duration": duration})
        return job_experiences

    def __parse_skills(self, resume_card) -> list[str]:
        """Витягує список навичок із резюме."""
        return [element.get_text(strip=True) for element in resume_card.find_all("span", class_="label-skill")]

    def _parse_resume(self, resume) -> dict[str, str | None]:
        """Парсить дані одного резюме."""
        data = {}
        data['linkURL'] = self.__parse_resume_link(resume)

        html = self.__fetch_html(data['linkURL'])
        if not html:
            return data

        soup = BeautifulSoup(html, "lxml")
        resume_card = soup.find("div", id=f"resume_{data['linkURL'].split('/')[-2]}")

        # Основні дані резюме
        resumeLink = resume.find('a')['href']
        data["id"] = re.search(r'\d+', resumeLink).group()
        data['resume_time'] = resume_card.find("time")["datetime"]
        data["name"] = resume_card.find("h1").text.strip()
        data.update(self.__parse_salary_and_position(resume_card))
        data.update(self.__parse_personal_info(resume_card))
        data['languages'] = self.__parse_languages(resume_card)
        data['experience'] = self.__parse_experience(resume_card)
        data['skills'] = self.__parse_skills(resume_card)

        return data

    def parse_all_resumes(self) -> list[dict[str, str | None]]:
        """Парсить всі резюме """
        page = 1
        all_resume_list = []
        experienceParameter = self.__experience_to_parameter(self.experience)
        while True:
            url = f'{self.base_url}?page={page}&{experienceParameter}'
            html = self.__fetch_html(url)
            if not html or page>20: # Якщо даних немає або кілкість сторінок більша за 20 - зупиняємося
                break

            soup = BeautifulSoup(html, "lxml")
            resume_list = soup.select("div.card.card-hover.card-search.resume-link.card-visited.wordwrap")

            if not resume_list:
                break

            for resume in resume_list:
                data = self._parse_resume(resume)
                print(data)
                if data:
                    all_resume_list.append(data)

            page += 1

        return all_resume_list

    def getResumes(self) -> list[dict[str, str | None]]:
        """Повертає резюме """
        all_resume_list = self.parse_all_resumes()
        return all_resume_list

