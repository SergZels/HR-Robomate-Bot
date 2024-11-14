from aiogram import Router, F, types
from aiogram.types import Message,ReplyKeyboardRemove
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
from init import bot
from parsers.workUAparser import WorkUaParser
from DataProcessor import DataProcessor
import keyboards
import asyncio

router = Router()


class AsyncFileHandler(logging.FileHandler):  # для асинхронного логування
    def emit(self, record):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, super().emit, record)


logger = logging.getLogger('async_logger')
logger.setLevel(logging.INFO)
handler = AsyncFileHandler('Logfile.txt')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Функція для обробки навичок
def format_skills(skills: list[str]) -> str:
    if not skills:
        return "не вказано"
    return " | ".join(skills)

# Функція для обробки зарплати
def format_salary(salary: str | None) -> str:
    return "не вказано" if salary is None else salary

async def parser_task(chat_id: int, exchange: str, specialization: str, experience: str,
                      location: str,skills:str, age: str, salary: str):

    if exchange == "workua":
        parser = WorkUaParser(position=specialization, experience=experience)
        resumes = parser.getResumes()

        # processor = DataProcessor(resumes)
        # filtered_data = processor.apply_filters(city_name=location, max_age=age)

        #sorted_data = processor.sort_by_price()

        for resume in resumes:
            keyboard = keyboards.build_keyboard(resume.get('linkURL'))
            formatted_skills = format_skills(resume.get('skills', []))
            formatted_salary = format_salary(resume.get('salary'))
            await bot.send_message(
                chat_id,
                f"<b>{resume.get('name')}</b> {resume.get('Вік:', '')}\n"
                f"<b>{resume.get('position')}</b> {resume.get('Місто:', '')}\n"
                f"<b>Навички</b>: {formatted_skills}\n"
                f"<b>Очікувана заробітня плата:</b> {formatted_salary}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await message.answer("Oберіть біржу 👇", reply_markup=keyboards.start_Keyboard.as_markup())
    await state.set_state(States.waiting_for_exchange)


class States(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_specialization = State()
    waiting_for_experience = State()
    waiting_for_location = State()
    waiting_for_age = State()
    waiting_for_skills = State()
    waiting_for_salary = State()
    go = State()


@router.callback_query(States.waiting_for_exchange)
async def exchange(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'workua':
        await callback.message.answer(f"Даний функціонал ще в розробці")
    else:
        await state.update_data(exchange=callback.data)
        await callback.message.answer(f"Напишіть 🖊 спеціалізацію наприклад: GO програміст")
        await state.set_state(States.waiting_for_specialization)


@router.message(States.waiting_for_specialization)
async def specialization(message: types.Message, state: FSMContext):
    await state.update_data(specialization=message.text)
    await message.answer(f"Оберіть 👇", reply_markup=keyboards.experience.as_markup())
    await state.set_state(States.waiting_for_location)


@router.callback_query(States.waiting_for_location)
async def location(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(experience=callback.data)
    await callback.message.answer(f"Напишіть місто проживання або натисніть Вся Україна",
                                  reply_markup=keyboards.location_keyboard)
    await state.set_state(States.waiting_for_age)

@router.message(States.waiting_for_age)
async def age(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await message.answer(f"Напишіть граничний вік наприклад 35", reply_markup=keyboards.age_keyboard)
    await state.set_state(States.waiting_for_skills)


@router.message(States.waiting_for_skills)
async def skills(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer(f"Напишіть необхідні навички через кому, наприклад: git, docker,...",
                                    reply_markup=ReplyKeyboardRemove())
    await state.set_state(States.waiting_for_salary)
@router.message(States.waiting_for_salary)
async def salary(message: types.Message, state: FSMContext):
    await state.update_data(skills=message.text)
    await message.answer(f"Введіть очікувану заробітню плату 💵 у грн. наприклад 100000",
                         reply_markup=keyboards.salary_keyboard)
    await state.set_state(States.go)


@router.message(States.go)
async def go(message: types.Message, state: FSMContext):
    await state.update_data(salary=message.text)
    data = await state.get_data()
    exchange = data.get("exchange")
    specialization = data.get("specialization")
    experience = data.get("experience")
    location = data.get("location")
    skills = data.get("skills")
    age = data.get("age")
    salary = data.get("salary")
    await message.answer(
        f"<b>Здійснюється пошук 🔍 за параметрами:</b>\n"
        f"<b>Біржа:</b> {exchange}\n"
        f"<b>Спеціалізація:</b> {specialization}\n"
        f"<b>Досвід:</b> {experience}\n"
        f"<b>Локація:</b> {location}\n"
        f"<b>Навички:</b> {skills}\n"
        f"<b>Вік:</b> {age}\n"
        f"<b>ЗП:</b> {salary}",
        parse_mode='HTML')
    await message.answer("Очікуйте! ⏳",  reply_markup=ReplyKeyboardRemove())
    await state.clear()

    # виклик парсера у фоні
    asyncio.create_task(parser_task(chat_id=message.chat.id,
                                    exchange=exchange,
                                    specialization=specialization,
                                    experience=experience,
                                    location=location,
                                    skills=skills,
                                    age=age, salary=salary))


@router.message(F.text.lower() == "/help")
async def answer_yes(message: Message):
    await message.answer("Для отримання допомоги напишіть будь-ласка на ...", )
