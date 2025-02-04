from os import getenv
from aiogram import Bot, Dispatcher, types, filters, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio
import LectureSearcher as ls
import ClassLibrary as cl
import pickle
import math


TOKEN = getenv('BOT_TOKEN')

dp = Dispatcher()

NEED_UPDATE = False
groups = dict()
if NEED_UPDATE:
    with open("group_dump.pickle", "wb") as file:
        groups = ls.load_all_data()
        pickle.dump(groups, file)
else:
    with open("group_dump.pickle", "rb") as file:
        groups = pickle.load(file)

COLUMNS = 4
ROWS = 4
ELEMENTS = COLUMNS * ROWS
PAGES = math.ceil(len(groups.keys())/(COLUMNS*ROWS))


class Form(StatesGroup):
    name = State()
    page = State()
    group = State()
    subgroup = State()


@dp.message(filters.Command('start'))
async def start(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, 'Здравствуйте!')
    await state.update_data(page=1)

    await get_name(message, state)


@dp.callback_query(F.data.in_(groups.keys()))
async def select_subgroup(call: types.callback_query, state: FSMContext):
    await state.update_data(group=call.data)

    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, 'Выберите вашу подгруппу:', reply_markup=get_subgroups_keyboard(groups[call.data]))


@dp.callback_query(F.data.contains('sg-'))
async def select_day(call: types.callback_query, state: FSMContext):
    await state.update_data(subgroup=call.data.replace('sg-', ''))

    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, 'Выберите день:', reply_markup=get_days_keyboard())


@dp.callback_query(F.data.in_(['next', 'prev']))
async def change_page(call: types.callback_query, state: FSMContext):
    data = await state.get_data()
    current_page = data['page']
    
    if data['page'] < PAGES and call.data == 'next' or data['page'] > 1 and call.data == 'prev':
        new_page = current_page+1 if call.data == 'next' else current_page-1
        await state.update_data(page=new_page)

        kb = get_groups_keyboard(new_page)
        await call.message.edit_text(text=f'{data["name"]}, выберите группу:', reply_markup=kb)

    await bot.answer_callback_query(call.id)


@dp.callback_query(F.data.in_(cl.Week.WEEK_TABLE))  # If data is in ['Monday', 'Tuesday'...]
async def send_lectures_day(call: types.callback_query, state: FSMContext):
    data = await state.get_data()

    group = data['group']
    subgroup = data['subgroup']
    day_index = cl.Week.WEEK_TABLE.index(call.data)    
    lecture_text = groups[group].weeks[0].days[day_index].get_all_lectures(subgroup)

    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, lecture_text)



@dp.message(filters.Command('groups'))
async def show_groups(message: types.Message, state: FSMContext):
    data = await state.get_data()

    kb = get_groups_keyboard(data['page'])
    await bot.send_message(message.chat.id, text=f'{data["name"]}, выберите группу:', reply_markup=kb)


@dp.message(Form.name, F.text.casefold() == 'да')
async def accept_name(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        await bot.send_message(message.chat.id, f'Приятно познакомиться, {data["name"]}', reply_markup=types.ReplyKeyboardRemove())
    except KeyError:
        await get_name(message, state)
    

@dp.message(Form.name, F.text.casefold() == 'нет')
async def decline_name(message: types.Message, state: FSMContext):
    await state.set_state(Form.name)
    await bot.send_message(message.chat.id, f'Введите ваше имя:')


@dp.message(Form.name)
async def update_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await state.set_state(Form.name)
    await bot.send_message(message.chat.id, 'Желаете ли вы оставить это имя?', reply_markup=types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text='Да'), types.KeyboardButton(text='Нет')]], resize_keyboard=True, one_time_keyboard=True))


async def get_name(message: types.Message, state: FSMContext):
    await state.set_state(Form.name)
    await bot.send_message(message.chat.id, 'Введите ваше имя:')


def get_groups_keyboard(page: int) -> types.InlineKeyboardMarkup:
    keyboard_builder = InlineKeyboardBuilder()

    for row in range(ROWS):
        keyboard_builder.row(*[types.InlineKeyboardButton(text=f'{group}', callback_data=group) for group in list(groups.keys())[(page-1)*ELEMENTS+COLUMNS*row:(page-1)*ELEMENTS+COLUMNS*(row+1)]])
    keyboard_builder.row(types.InlineKeyboardButton(text='<-', callback_data='prev'), types.InlineKeyboardButton(text=f'{page}/{PAGES}', callback_data='page'), types.InlineKeyboardButton(text='->', callback_data='next'))

    return keyboard_builder.as_markup()


def get_days_keyboard() -> types.InlineKeyboardMarkup:
    keyboard_builder = InlineKeyboardBuilder()

    for day in cl.Week.WEEK_TABLE:
        keyboard_builder.add(types.InlineKeyboardButton(text=day, callback_data=day))
    
    return keyboard_builder.as_markup()


def get_subgroups_keyboard(group: cl.Group) -> types.InlineKeyboardButton:
    keyboard_builder = InlineKeyboardBuilder()

    for subgroup in group.subgroups:
        keyboard_builder.add(types.InlineKeyboardButton(text=subgroup, callback_data=f'sg-{subgroup}'))

    return keyboard_builder.as_markup()
    

bot = Bot(token=TOKEN)
async def main() -> None:
    await dp.start_polling(bot)


print('Here')
asyncio.run(main())