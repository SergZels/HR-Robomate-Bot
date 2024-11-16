from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from init import bot, redis
from parsers.workUAparser import WorkUaParser
from DataProcessor import DataProcessor, format_salary, format_skills
import keyboards
import asyncio
import json
from hashlib import sha256

router = Router()


async def parser_task(chat_id: int, exchange: str, specialization: str, experience: str,
                      location: str, skills: str, salary: str):
    """Повертає топ 5 резюме  в боті та лінк на інші
     Дана функція буде запускатися у новому треді, отже асинхронний цикл не буде заблоковано
     для збільшення продуктивності додаю кешування
     топ 5 кандидатів виводим в боті, багато в боті реально не зручно!
     інших на сторінці за зсилкою
     """

    cache_key = sha256(
        f"{exchange}:{specialization}:{experience}:{location}:{skills}:{salary}".encode()).hexdigest()

    cached_data = await redis.get(cache_key)

    if cached_data:
        resumes = json.loads(cached_data)
    else:
        # Якщо даних немає в кеші, викликаємо парсер
        if exchange == "workua":
            parser = WorkUaParser(position=specialization, experience=experience)
            resumes = parser.getResumes()  # парсимо по параметрах
            processor = DataProcessor(resumes)
            filtered_data = processor.apply_filters(city_name=location, max_salary=salary)  # фільтуємо
            processedResumes = processor.pointsDetermination(skills=skills,
                                                             filtered_data=filtered_data)  # виставляємо бали
            processedResumes = processedResumes[:20]  # відбираємо топ 20 (гадаю цього достатньо)
            await redis.setex(cache_key, 60 * 60, json.dumps(processedResumes))

    await bot.send_message(chat_id, "Ось ТОП 5 🏆 кандидатів на дану посаду!")
    for resume in processedResumes[:5]:  # виводимо топ 5 інші за посиланням, це для зручносі
        keyboard = keyboards.build_keyboard(resume.get('linkURL'))
        formatted_skills = format_skills(resume.get('skills', []))
        formatted_salary = format_salary(resume.get('salary'))
        await bot.send_message(
            chat_id,
            f"<b>{resume.get('name')}</b> {resume.get('Вік:', '')} {resume.get('Місто:', '')} <b>Балів: </b>{resume.get('points', '')}\n"
            f"<b>{resume.get('position')}</b> \n"
            f"<b>Навички</b>: {formatted_skills}\n"
            f"<b>Очікувана заробітня плата:</b> {formatted_salary}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await bot.send_message(chat_id,
                           f"Переглянути більше кандидатів можна за посиланням: http://zelse.asuscomm.com:5000?cache_key={cache_key}\n"
                           f"Успіхів у пошуку нового співробітника 🧑‍💻!",
                           parse_mode="HTML", disable_web_page_preview=True)


# ----------------------------бот-------------------------------------------------
@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await message.answer("Вітаю✋! Я HR помічник👩‍💼! Я допоможу тобі знайти 🔍 необхідного кандидата!")
    await message.answer("Oберіть біржу праці 👇", reply_markup=keyboards.start_Keyboard.as_markup())
    await state.set_state(States.waiting_for_exchange)


# -------------------машина станів--------------------------------------------------
class States(StatesGroup):
    waiting_for_exchange = State()
    waiting_for_specialization = State()
    waiting_for_experience = State()
    waiting_for_location = State()
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
    await message.answer(f"Оберіть рівень досвіду 👇", reply_markup=keyboards.experience.as_markup())
    await state.set_state(States.waiting_for_location)


@router.callback_query(States.waiting_for_location)
async def location(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(experience=callback.data)
    await callback.message.answer(
        f"Вкажіть місто проживання для роботи в офісі або оберіть 'Вся Україна' для віддаленої роботи.",
        reply_markup=keyboards.location_keyboard)
    await state.set_state(States.waiting_for_skills)


@router.message(States.waiting_for_skills)
async def skills(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await message.answer(f"Напишіть очікувані навички через кому, наприклад: git, docker,...",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(States.waiting_for_salary)


@router.message(States.waiting_for_salary)
async def salary(message: types.Message, state: FSMContext):
    await state.update_data(skills=message.text)
    await message.answer(f"Введіть пропоновану заробітню плату 💵 у грн. наприклад 100000",
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
    salary = data.get("salary")


    await message.answer(
        f"<b>Здійснюється пошук 🔍 за параметрами:</b>\n"
        f"<b>Біржа:</b> {exchange}\n"
        f"<b>Спеціалізація:</b> {specialization}\n"
        f"<b>Досвід:</b> {experience}\n"
        f"<b>Локація:</b> {location}\n"
        f"<b>Навички:</b> {skills}\n"
        f"<b>ЗП:</b> {salary}",
        parse_mode='HTML')
    await message.answer("Очікуйте! ⏳", reply_markup=ReplyKeyboardRemove())
    await state.clear()

    # виклик парсера у фоні
    asyncio.create_task(parser_task(chat_id=message.chat.id,
                                    exchange=exchange,
                                    specialization=specialization,
                                    experience=experience,
                                    location=location,
                                    skills=skills,
                                    salary=salary))


@router.message(F.text.lower() == "/help")
async def answer_yes(message: Message):
    await message.answer("Для отримання допомоги напишіть будь-ласка на ...", )#можна вказати нік підтримки
