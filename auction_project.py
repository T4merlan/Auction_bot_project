import telebot
from telebot import types
import os
import threading
import time

context = {}
user_started = {}
timers = {}
bot = telebot.TeleBot('BOT_TOKEN')
# MY_BOT_TOKEN 6904302308:AAGXb89Ds6hKmTtPvXeJ82dlgPikcRsDJ4M
user_selected_time = {}
context1 = {}

# Set folder name
folder_name = 'photos'

# Checks if folder already exists
if not os.path.exists(folder_name):
    os.makedirs(folder_name)
    print(f"folder {folder_name} was created.")
else:
    print(f"folder {folder_name} already exists.")


def is_admin(chat_id, user_id):
    return user_id == 278853856 and chat_id == 278853856


@bot.message_handler(commands=['help'])
def new_command_handler(message):
    bot.send_message(message.chat.id, '1.start using the command /start\n2.select the button you need!\n')
    user_started[message.chat.id] = True


@bot.message_handler(commands=['start', 'restart'])
def main(message):
    bot.send_message(message.chat.id, 'Hello, Iam Auction_Bot\n')
    user_started[message.chat.id] = True
    send_photo_with_new_buttons(message)


@bot.inline_handler(lambda query: True)
def handle_inline(query):
    try:
        user_id = query.from_user.id
        price = context.get(user_id, {}).get('price')
        description = context.get(user_id, {}).get('description')
        currency = context.get(user_id, {}).get('currency')

        inline_message_id = query.id
        context1[query.from_user.id] = {'inline_message_id': inline_message_id}
        article_photo = types.InlineQueryResultPhoto(
            id='1',
            title='Send a photo from a bot',
            thumbnail_url='https://i.ibb.co/wSyWtPF/78pcl215365748748198-l.jpg',
            caption=f"Price: {price} {currency}\nDescription: {description}",
            photo_url='https://i.ibb.co/wSyWtPF/78pcl215365748748198-l.jpg',
        )
        article_text = types.InlineQueryResultArticle(
            id='2',
            title='Send a message from a bot',
            input_message_content=types.InputTextMessageContent(
                message_text=f"Price: {price} {currency}\nDescription: {description}"
            ),
        )

        bot.answer_inline_query(query.id, [article_photo, article_text])
    except Exception as e:
        print(e)


def send_photo_with_new_buttons(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Create an auction', callback_data='auction')
    if has_time_passed(message.chat.id):
        btn3 = types.InlineKeyboardButton('my auctions', callback_data='own', callback_game=True)
        markup.row(btn3)
    markup.row(btn1)
    photo_path = 'auction_stock.jpg'
    with open(photo_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo, ':', reply_markup=markup)


def has_time_passed(chat_id):
    current_time = time.time()
    end_time = get_end_time_for_user(chat_id)

    return current_time >= end_time


def start_new_auction(message):
    bot.send_message(message.chat.id, 'describe a load')
    user_started[message.chat.id] = True
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    bot.register_next_step_handler(message, process_description)


def process_description(message):
    description = message.text
    try:
        save_to_context(message.chat.id, 'description', description)
    except ValueError:
        print('Error')
    bot.send_message(message.chat.id, f'You described the load as:\n{description}')
    bot.send_message(message.chat.id, 'Please enter a price')
    bot.register_next_step_handler(message, process_price_and_currency)


def process_price_and_currency(call):
    try:
        user_input = call.text
        cleaned_input = ''.join(c if c.isdigit() or c == '.' else '' for c in user_input)
        price = float(cleaned_input)
        if price <= 0:
            raise ValueError("Invalid price")
        save_to_context(call.chat.id, 'price', price)
        choose_currency(call)
    except ValueError:
        bot.send_message(call.chat.id,
                         'Incorrect price entered. Please enter a valid number greater than 0')
        bot.clear_step_handler_by_chat_id(chat_id=call.chat.id)
        bot.register_next_step_handler(call, process_price_and_currency)


def choose_currency(call):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('UZS', callback_data='uzs')
    btn2 = types.InlineKeyboardButton('EUR', callback_data='eur')
    btn3 = types.InlineKeyboardButton('USD', callback_data='usd')
    btn4 = types.InlineKeyboardButton('RUB', callback_data='rub')
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    bot.send_message(call.chat.id, 'Choose the preferred currency', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.message is not None)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    try:
        if call.data == 'auction':
            start_new_auction(call.message)
        elif call.data == 'own':
            buttons_auction(call.message)
        elif call.data in ['uzs', 'eur', 'usd', 'rub']:
            currency = call.data.upper()
            price = context.get(call.message.chat.id, {}).get('price')
            if call.data in ['uzs', 'eur', 'usd', 'rub']:
                save_to_context(call.message.chat.id, 'currency', currency)
                save_to_context(call.message.chat.id, 'price', price)

                bot.send_message(call.message.chat.id, f'You selected {currency} with a price of {price}')
                bot.send_message(call.message.chat.id, 'Send a photo:')
            else:
                bot.send_message(call.message.chat.id, 'Error occurred.Try again')

        elif call.data in ['10s', '1m', '10m', '1h', '3h', '6h', '12h', '1d', '3d']:
            time_choice = call.data
            bot.send_message(call.message.chat.id, f'You selected👉 {time_choice}.'
                                                   f'The auction will end in {time_choice}.')
            # Cancel the previous timer, if any
            if call.message.chat.id in timers:
                timers[call.message.chat.id].cancel()

            # Convert time_choice to seconds
            if time_choice.endswith('s'):
                time_seconds = int(time_choice[:-1]) * 1
            elif time_choice.endswith('m'):
                time_seconds = int(time_choice[:-1]) * 60
            elif time_choice.endswith('h'):
                time_seconds = int(time_choice[:-1]) * 3600
            elif time_choice.endswith('d'):
                time_seconds = int(time_choice[:-1]) * 86400
            else:
                bot.send_message(call.message.chat.id, 'Invalid time choice. Please try again.')
                return

            # Schedule the auction end callback function
            timers[call.message.chat.id] = threading.Timer(
                time_seconds,
                auction_end_callback,
                args=[call.message.chat.id]
            )
            timers[call.message.chat.id].start()
            buttons_auction(call.message)
        elif call.data in ['btn2', 'btn3', 'btn4', 'btn5', 'btn6']:

            price_mapping = {'btn2': 100, 'btn3': 1000, 'btn4': 2000, 'btn5': 3000, 'btn6': 5000}
            price_increment = price_mapping.get(call.data, 0)
            save_to_context(call.message.chat.id, 'price_increment', price_increment)

            current_price = context.get(chat_id, {}).get('price', 0)
            new_price = current_price + price_increment
            save_to_context(chat_id, 'price', new_price)
            update_share_button_price(chat_id, new_price)
            user_id = call.from_user.id
            save_to_context(chat_id, 'last_bidder', user_id)
            message_text = (
                f"price: {new_price} {context[chat_id]['currency']}\n"
                f"description: {context[chat_id]['description']}"
            )
            context[chat_id]['message_text'] = message_text

            buttons_auction(call.message)
        else:
            bot.send_message(call.message.chat.id, 'Invalid option. Please try again.')

    except ValueError:
        bot.send_message(call.message.chat.id, 'Oops! Something went wrong. Please try again.')


@bot.message_handler(content_types=['photo'])
def get_photo(message):
    try:
        user_id = message.from_user.id
        user_info = bot.get_chat_member(message.chat.id, user_id)
        username = user_info.user.username if user_info.user.username else f'User{user_id}'
        if 'inline_message_id' in context1.get(user_id, {}):
            return
        # Assuming there is only one photo in the message
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)

        photo_directory = "photos"
        if not os.path.exists(photo_directory):
            os.makedirs(photo_directory)

        # Save the photo to a file
        photo_path = f"photos/{file_id}.jpg"  # Specify your desired path and filename
        with open(photo_path, 'wb') as new_file:
            new_file.write(file)

        # Extract data from the context
        price = context.get(message.chat.id, {}).get('price')
        description = context.get(message.chat.id, {}).get('description')
        currency = context.get(message.chat.id, {}).get('currency')
        photo_data = {
            'price': price,
            'description': description,
            'currency': currency,
            'photo_path': photo_path,
        }

        # Save the photo data to the context
        save_to_context(message.chat.id, 'photo_data', photo_data)

        # Create a message with the data
        message_text = f"Price: {price} {currency}\nDescription: {description}"

        # Send the photo with the message
        with open(photo_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=message_text)
        save_to_context(message.chat.id, 'last_bidder', username)
        # Proceed to the next step (choose_time)
        choose_time(message)

    except Exception as e:
        bot.send_message(message.chat.id, f'Oops! Something went wrong: {str(e)}')


def delete_photos_after_delay(photo_directory, delay_seconds):
    photo_files = [f for f in os.listdir(photo_directory) if os.path.isfile(os.path.join(photo_directory, f))]
    current_time = time.time()

    for photo_file in photo_files:
        file_path = os.path.join(photo_directory, photo_file)
        file_creation_time = os.path.getctime(file_path)

        if current_time - file_creation_time > delay_seconds:
            os.remove(file_path)
            print(f"Файл {photo_file} удален.")


delete_photos_after_delay("photos", 24 * 60 * 60)


def auction_end_callback(chat_id):
    try:
        # Function to be called when the auction ends
        bot.send_message(chat_id, 'The auction has ended!')
        winning_price = context[chat_id].get('price', 0)
        description = context[chat_id].get('description', 'No load information')
        last_bidder_id = context[chat_id].get('last_bidder')
        last_bidder_info = bot.get_chat_member(chat_id, last_bidder_id) if last_bidder_id else None
        last_bidder_username = (
            last_bidder_info.user.username if last_bidder_info and last_bidder_info.user.username else 'Unknown member'
        )
        last_bidder_contact = f"@{last_bidder_username}"
        inline_markup = types.InlineKeyboardMarkup()
        processed_description = description.replace('\n', ' ')
        share_button = types.InlineKeyboardButton(
            'Share',
            switch_inline_query=f"+{winning_price + context[chat_id]['price_increment']} "
                                f"{processed_description}{last_bidder_contact}"
        )
        inline_markup.add(share_button)
        message_id = context[chat_id].get('sent_message_id')
        if message_id:
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=inline_markup)
        winning_price = context[chat_id].get('price', 0)
        currency = context[chat_id].get('currency', 'Unknown currency')
        description = context[chat_id].get('description', 'There is no information about the car')
        last_bidder_id = context[chat_id].get('last_bidder')
        last_bidder_info = bot.get_chat_member(chat_id, last_bidder_id) if last_bidder_id else None
        last_bidder_username = (
            last_bidder_info.user.username if last_bidder_info and last_bidder_info.user.username else 'Unknown member'
        )
        last_bidder_contact = f"@{last_bidder_username}"
        bot.send_message(chat_id, f'congratulations {last_bidder_contact} you wo n in the auction!\n'
                                  f'The price: {winning_price} {currency}\n'
                                  f'The load: {description}')
    except Exception as e:
        print(f'Error updating share button text": {e}')


def choose_time(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('10s', callback_data='10s')
    btn2 = types.InlineKeyboardButton('1 min', callback_data='1m')
    btn3 = types.InlineKeyboardButton('10 min', callback_data='10m')
    markup.row(btn1, btn2, btn3)
    btn4 = types.InlineKeyboardButton('1 hour', callback_data='1h')
    btn5 = types.InlineKeyboardButton('3 hours', callback_data='3h')
    btn6 = types.InlineKeyboardButton('6 hours', callback_data='6h')
    markup.row(btn4, btn5, btn6)
    btn7 = types.InlineKeyboardButton('12 hours', callback_data='12h')
    btn8 = types.InlineKeyboardButton('1 day', callback_data='1d')
    btn9 = types.InlineKeyboardButton('3 days', callback_data='3d')
    markup.row(btn7, btn8, btn9)
    bot.send_message(message.chat.id, 'select the time after which the bot will end the auction:', reply_markup=markup)
    user_selected_time[message.chat.id] = True


def update_share_button_price(chat_id, new_price):
    try:
        message_id = context.get(chat_id, {}).get('sent_message_id')
        if message_id:
            inline_markup = types.InlineKeyboardMarkup()
            context[chat_id]['price'] = new_price
            processed_context = context[chat_id]['message_text'].replace('\n', ' ')
            share_button = types.InlineKeyboardButton(
                'Share',
                switch_inline_query=f"+{new_price + context[chat_id]['price_increment']} "
                                    f"{processed_context}"
            )
            inline_markup.add(share_button)
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=inline_markup)
            bot.edit_message_caption(caption=f"Price: {new_price} {context[chat_id]['currency']}", chat_id=chat_id,
                                     message_id=message_id)
    except Exception as e:
        print(f'Error updating share button text": {e}')


def buttons_auction(message):
    photo_data = context.get(message.chat.id, {}).get('photo_data')
    if not photo_data:
        bot.send_message(message.chat.id, "Photo data not found in context.")
        return
    price = context[message.chat.id]['price']
    currency = photo_data['currency']
    description = photo_data['description']
    message_text = f"price: {price} {currency}\ndescription: {description}"
    context[message.chat.id]['message_text'] = message_text
    inline_markup = types.InlineKeyboardMarkup()
    share_button = types.InlineKeyboardButton(
        'Share',
        switch_inline_query=f"+{context[message.chat.id]['price_increment']} {message_text}"
    )
    btn2 = types.InlineKeyboardButton('+100', callback_data='btn2')
    btn3 = types.InlineKeyboardButton('+1000', callback_data='btn3')
    btn4 = types.InlineKeyboardButton('+2000', callback_data='btn4')
    btn5 = types.InlineKeyboardButton('+3000', callback_data='btn5')
    btn6 = types.InlineKeyboardButton('+5000', callback_data='btn6')
    inline_markup.add(share_button)
    inline_markup.row(btn2, btn3, btn4, btn5, btn6)

    sent_message = bot.send_photo(message.chat.id, open(photo_data['photo_path'], 'rb'), reply_markup=inline_markup)

    save_to_context(message.chat.id, 'sent_message_id', sent_message.message_id)


def get_end_time_for_user(chat_id):
    return context.get(chat_id, {}).get('end_time', 0)


def save_to_context(chat_id, key, value):
    if chat_id not in context:
        context[chat_id] = {}
    context[chat_id].setdefault('price_increment', 0)
    context[chat_id][key] = value


bot.polling(none_stop=True)
