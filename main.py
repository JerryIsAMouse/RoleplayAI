from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json
import os
import httpx
from keep_alive import keep_alive
keep_alive()

import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or "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"

async def get_openrouter_reply(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://your-app.com",  # customize this if needed
        "X-Title": "RoleplayAI",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",  # or gpt-3.5 or another supported model
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("❌ OpenRouter API error:", e)
        return None


story_mode_state = {}  # Tracks if user is writing a custom story
character_creation_state = {}
user_setup_state = {}
nsfw_state = {}


# Load or initialize memory and user data
USER_DATA_FILE = "user_data.json"
MEMORY_FILE = "memory.json"

if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
else:
    memory = {}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def save_user_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=2)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    intro_text = (
        "🌟 *Welcome to RoleplayAI - v1.0!* 🌟\n\n"
        "🎭 *What is RoleplayAI?*\n"
        "RoleplayAI is your immersive AI storytelling partner. It lets you create custom characters, define a relationship, choose a storyline, and chat in real-time as if you're inside a story!\n\n"
        "✨ *What you can do:*\n"
        "• Create your own character and backstory\n"
        "• Chat with your character in a live roleplay format\n"
        "• Choose between writing your own story or generating one\n"
        "• Enable or disable NSFW content\n\n"
        "📜 *Commands:*\n"
        "• `/start` - Begin or continue setup\n"
        "• `/reset` - Reset *all* your data\n"
        "• `/resetstory` - Clear only the story & memory\n\n"
        "⚠️ *Disclaimer:*\n"
        "• This is the *first version* of RoleplayAI, and it's still improving.\n"
        "• 🕓 *Please be patient* while stories and replies are being generated. It might take a few seconds due to our limitations.\n"
        "• We appreciate your understanding ❤️\n\n"
        "🚀 Click on *'Let's Begin 👉'* to begin your journey?"
    )

    keyboard = [["Let's Begin 👉"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(intro_text, reply_markup=reply_markup, parse_mode="Markdown")

    # Set flag so the next reply continues to user setup
    user_setup_state[user_id] = {"step": "name"}



async def story_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Write My Own", "Auto Generate"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("📖 How would you like to begin your story?", reply_markup=reply_markup)


# /reset command - resets everything
async def reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Delete user data and memory
    user_data.pop(user_id, None)
    memory.pop(user_id, None)
    story_mode_state.pop(user_id, None)

    save_user_data()
    save_memory()

    await update.message.reply_text("♻️ All your data has been reset. Use /start to begin again.")

# /resetstory command - clears memory + story only
async def reset_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id in user_data:
        user_data[user_id].pop("user_story", None)
        user_data[user_id].pop("generated_story", None)
        story_mode_state[user_id] = None  # Let them pick story again
        save_user_data()

    memory[user_id] = []
    save_memory()

    await update.message.reply_text("🧹 Story and memory cleared. Please choose a new story:")
    await story_mode(update, context)

async def handle_story_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    choice = update.message.text.strip().lower()

    if choice == "write my own":
        story_mode_state[user_id] = "manual"
        await update.message.reply_text("✍️ Please type your story:", reply_markup=ReplyKeyboardRemove())

    elif choice == "auto generate":
        story_mode_state[user_id] = None  # Clear state just in case
        await update.message.reply_text("🪄 Generating your story... (Please be patient)")

        profile = user_data.get(user_id)
        if not profile:
            await update.message.reply_text("❗ Please create your character first using /start.")
            return

        characters = profile.get("characters", [])
        user_name = profile.get("name", "You")
        user_gender = profile.get("gender", "unknown")
        nsfw = profile.get("nsfw", False)

        char_list = ""
        for c in characters:
            char_list += f"""
- {c['name']} ({c['gender']}), {c['profession']}, likes {c['interests']}, body: {c['body_type']}, relation: {c['relation']}, detail: {c['description']}"""

        prompt = f"""Create a roleplay story with the characters below. But don't use any "**" marks for the messages, just use brackets for the plot. Use easy, understandable language for everyone. Don't say anything as the user or ask what to do next,just play the character. Use this style:

(story and what's going on)

Character: <talks> (scene, environment, feelings – short and realistic)

User: {user_name} ({user_gender}), NSFW: {'on' if nsfw else 'off'}

Characters:{char_list}

Now begin the chat directly."""

        try:
            reply = await get_openrouter_reply(prompt)
            if not reply:
                raise Exception("OpenRouter returned empty reply")

            user_data[user_id]["generated_story"] = reply  # Save full story
            memory.setdefault(user_id, []).append(reply)

            save_user_data()
            save_memory()

            await update.message.reply_text(reply)

        except Exception as e:
            print("❌ Auto story gen error:", e)
            await update.message.reply_text("⚠️ Failed to generate story.")

    else:
        await update.message.reply_text("Please choose either 'Write My Own' or 'Auto Generate'.")

async def handle_manual_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Only continue if user is in story writing mode
    if story_mode_state.get(user_id) != "manual":
        return  # Ignore

    story = update.message.text.strip()
    if not story:
        await update.message.reply_text("✍️ Please write a story to continue.")
        return

    # Make sure the user has a profile and characters
    profile = user_data.get(user_id)
    if not profile or "characters" not in profile or not profile["characters"]:
        await update.message.reply_text("❗ Please set up your character first before writing a story.")
        return

    # Save and exit manual mode
    user_data[user_id]["user_story"] = story
    story_mode_state[user_id] = None
    save_user_data()

    characters = profile["characters"]
    user_name = profile.get("name", "You")
    user_gender = profile.get("gender", "unknown")
    nsfw = profile.get("nsfw", False)

    # Build the story prompt
    prompt = f"""You are inside a Telegram roleplay story. Never say you're an AI. But don't use any "**" marks for the messages, just use brackets for the plot. Use easy, understandable language for everyone. Don't say anything as the user or ask what to do next,just play the character.

Start the first message in this format:

(plot or story)

Character: talks (scene, environment, feelings – short and human)

User: {user_name} ({user_gender}), NSFW: {'on' if nsfw else 'off'}

Characters:"""

    for c in characters:
        prompt += f"""
- {c['name']} ({c['gender']}), {c['profession']}, likes {c['interests']}, body: {c['body_type']}, relation: {c['relation']}, detail: {c['description']}"""

    prompt += f"""

User's custom story:
{story}

Start the chat now. Use simple, human language."""

    try:
        reply = await get_openrouter_reply(prompt)
        if not reply:
            raise Exception("Empty reply from OpenRouter")

        user_data[user_id]["generated_story"] = reply
        memory.setdefault(user_id, []).append(reply)
        save_user_data()
        save_memory()

        await update.message.reply_text(reply)

    except Exception as e:
        print("❌ Manual story error:", e)
        await update.message.reply_text("⚠️ Failed to start story.")



# Chat message handler
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_msg = update.message.text.strip()

    if user_id not in user_data:
        await update.message.reply_text("❗ Please set up your character and story in the main RoleplayAI bot first.")
        return

    profile = user_data[user_id]
    memory.setdefault(user_id, [])
    recent_memory = memory[user_id][-5:]

    characters = profile.get("characters", [])
    story = profile.get("user_story") or profile.get("generated_story", "")
    user_name = profile.get("name", "You")
    user_gender = profile.get("gender", "unknown")
    nsfw = profile.get("nsfw", False)

    if not characters or not story:
        await update.message.reply_text("❗ Please set up your character and story first using /start.")
        return

    # Build prompt
    prompt = f"""You are inside a Telegram roleplay chat. Never say you're an AI. Stay in-character always.
Use a natural, emoji-friendly tone like Instagram messaging. But don't use any "**" marks for the messages, just use brackets for the plot. Use easy, understandable language for everyone. Don't say anything as the user or ask what to do next,just play the character.

ONLY use this format:

1. With plot and talk:
(scene or what's happening)

Character: message

(next part of plot or what's happening)

2. Only message:
Character: message

(short feeling or moment)

Never write what the user says. User is named {user_name} ({user_gender}). NSFW mode is {'on' if nsfw else 'off'}.

Characters:"""

    for char in characters:
        prompt += f"""
- {char['name']} ({char['gender']}), {char['profession']}, likes {char['interests']}, body: {char['body_type']}, relation: {char['relation']}, detail: {char['description']}"""

    prompt += f"""

Story context:
{story}

Recent memory:"""

    for msg in recent_memory:
        prompt += f"\n{msg}"

    prompt += f"\n\nUser: \"{user_msg}\"\nReply from the character in the proper format."

    try:
        reply = await get_openrouter_reply(prompt)
        if not reply:
            raise Exception("OpenRouter returned empty reply")

        memory[user_id].append(f'User: {user_msg}')
        memory[user_id].append(reply)
        if len(memory[user_id]) > 20:
            memory[user_id] = memory[user_id][-10:]

        save_memory()
        await update.message.reply_text(reply)

    except Exception as e:
        print("❌ AI error:", e)
        await update.message.reply_text("⚠️ Failed to generate a reply. Please try again later.")


async def handle_user_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text.strip()
    state = user_setup_state.get(user_id, {})

    if state.get("step") == "name":
        user_data.setdefault(user_id, {})["name"] = msg
        user_setup_state[user_id]["step"] = "gender"
        keyboard = [["Male", "Female", "Other"]]
        await update.message.reply_text("🚻 What is your gender?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif state.get("step") == "gender":
        if msg.lower() in ["male", "female"]:
            user_data[user_id]["gender"] = msg
            del user_setup_state[user_id]
            save_user_data()
            character_creation_state[user_id] = {"step": "name"}
            await update.message.reply_text("👤 Let's create your character!\n\nWhat's your character's name?", reply_markup=ReplyKeyboardRemove())
        elif msg.lower() == "other":
            user_setup_state[user_id]["step"] = "custom_gender"
            await update.message.reply_text("Please type your gender:", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("Please choose: Male, Female, or Other.")

    elif state.get("step") == "custom_gender":
        user_data[user_id]["gender"] = msg
        del user_setup_state[user_id]
        save_user_data()
        character_creation_state[user_id] = {"step": "name"}
        await update.message.reply_text("👤 Let's create your character!\n\nWhat's your character's name?")


async def handle_character_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text.strip()
    state = character_creation_state.get(user_id)

    if not state:
        return await dynamic_router(update, context)  # fallback to chat/manual

    step = state["step"]
    data = state.setdefault("data", {})

    if step == "name":
        data["name"] = msg
        state["step"] = "gender"
        keyboard = [["Male", "Female", "Other"]]
        await update.message.reply_text("What is your character's gender?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    elif step == "gender":
        if msg.lower() in ["male", "female"]:
            data["gender"] = msg
            state["step"] = "interests"
            await update.message.reply_text("What are your character's interests?", reply_markup=ReplyKeyboardRemove())
        elif msg.lower() == "other":
            state["step"] = "custom_gender"
            await update.message.reply_text("Please type your custom gender:")
        else:
            await update.message.reply_text("Please choose: Male, Female, or Other.")
    elif step == "custom_gender":
        data["gender"] = msg
        state["step"] = "interests"
        await update.message.reply_text("What are your character's interests?")
    elif step == "interests":
        data["interests"] = msg
        state["step"] = "profession"
        await update.message.reply_text("What is your character's profession?")
    elif step == "profession":
        data["profession"] = msg
        state["step"] = "relation"
        await update.message.reply_text("What is their relationship to you? (e.g. friend, lover, partner)")
    elif step == "relation":
        data["relation"] = msg
        state["step"] = "body_type"
        await update.message.reply_text("What is your character's body type?")
    elif step == "body_type":
        data["body_type"] = msg
        state["step"] = "description"
        await update.message.reply_text("Give a short backstory or personality description:")
    elif step == "description":
        data["description"] = msg

        # Save character
        character = data.copy()
        user_data.setdefault(user_id, {})
        user_data[user_id]["characters"] = [character]
        save_user_data()

        character_creation_state.pop(user_id)
        nsfw_state[user_id] = True  # move to nsfw setup state

        keyboard = [["Yes ✅", "No ❌"]]
        await update.message.reply_text("🔞 Do you want NSFW content in your story?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))



def is_in_manual_mode(user_id):
    return story_mode_state.get(user_id) == "manual"


async def dynamic_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text.strip()

    # Step 0: Handle NSFW toggle (before anything else)
    if user_id in nsfw_state:
        if msg.lower() in ["yes", "yes ✅"]:
            user_data.setdefault(user_id, {})["nsfw"] = True
        else:
            user_data.setdefault(user_id, {})["nsfw"] = False

        save_user_data()
        nsfw_state.pop(user_id)
        await update.message.reply_text("✅ NSFW preference saved!", reply_markup=ReplyKeyboardRemove())
        return await story_mode(update, context)

    # Step 1: If the user tapped "Let's Begin 👉"
    if msg == "Let's Begin 👉":
        user_setup_state[user_id] = {"step": "name"}
        return await update.message.reply_text("🙋 What is your name?")

    # Step 2: Collect user info
    if user_id in user_setup_state:
        await handle_user_setup(update, context)

    # Step 3: Character creation
    elif user_id in character_creation_state:
        await handle_character_creation(update, context)

    # Step 4: Story or chat
    elif is_in_manual_mode(user_id):
        await handle_manual_story(update, context)
    else:
        await chat(update, context)



# Launch bot
if __name__ == "__main__":
    app = ApplicationBuilder().token("8119403818:AAEgtkU0Mo1b8ICWM26QqdG-dOAEUDhpURw").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("story", story_mode))
    app.add_handler(CommandHandler("reset", reset_all))
    app.add_handler(CommandHandler("resetstory", reset_story))
    app.add_handler(MessageHandler(filters.Regex("^(Write My Own|Auto Generate)$"), handle_story_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_character_creation))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dynamic_router))

    print("🚀 Bot is running...")
    app.run_polling()
