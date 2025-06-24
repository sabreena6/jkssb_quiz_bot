from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get bot token from .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

QUIZ_FILE = "quizzes.json"
SCORE_FILE = "scores.json"

# ✅ Add your Telegram user ID here
ADMINS = [856668017]  # Replace with your Telegram ID

# Load quiz questions from file
def load_quizzes():
    if os.path.exists(QUIZ_FILE):
        with open(QUIZ_FILE, "r") as f:
            return json.load(f)
    return {"questions": []}

# Save quiz questions to file
def save_quizzes(quizzes):
    with open(QUIZ_FILE, "w") as f:
        json.dump(quizzes, f)

# Load scores from file
def load_scores():
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, "r") as f:
            return json.load(f)
    return {}

# Save scores to file
def save_scores(scores):
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id in ADMINS

    message = (
        "👋 Welcome to the JKSSB Toppers Quiz Bot!\n"
        "🎯 Practice JKSSB quiz questions created by toppers.\n"
        "📋 Type /quiz to begin a quiz.\n"
        "📊 Type /leaderboard to see top scorers."
    )

    if is_admin:
        message += (
            "\n\n🛠 You are an admin.\n"
            "📥 Send your questions in this format:\n"
            "Question?\n"
            "A. Option A\n"
            "B. Option B\n"
            "C. Option C\n"
            "D. Option D\n"
            "Answer: A"
        )
    else:
        message += "\n\n🆘 For help, type /help"

    await update.message.reply_text(message)

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Show welcome message\n"
        "/quiz - Start saved quiz\n"
        "/leaderboard - Show top scorers"
    )

# Start the quiz
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quizzes = load_quizzes().get("questions", [])
    context.user_data["quizzes"] = quizzes
    context.user_data["index"] = 0
    context.user_data["score"] = 0

    if not quizzes:
        await update.message.reply_text("🚫 No quizzes available.")
        return

    await send_question(update, context)

# Send one question at a time
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data["index"]
    quizzes = context.user_data["quizzes"]

    if index < len(quizzes):
        q = quizzes[index]
        await update.message.reply_text(
            f"{q['question']}\nA. {q['a']}\nB. {q['b']}\nC. {q['c']}\nD. {q['d']}"
        )
    else:
        await update.message.reply_text(f"✅ Quiz finished! Your score: {context.user_data['score']}")
        scores = load_scores()
        user = update.effective_user.first_name
        scores[user] = scores.get(user, 0) + context.user_data["score"]
        save_scores(scores)

# Handle answers and admin question input
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Admin adds a question
    if user_id in ADMINS and "Answer:" in text:
        try:
            parts = text.split("\n")
            question = parts[0]
            a = parts[1][3:].strip()
            b = parts[2][3:].strip()
            c = parts[3][3:].strip()
            d = parts[4][3:].strip()
            answer = parts[5].split(":")[1].strip().upper()

            quizzes = load_quizzes()
            quizzes["questions"].append({
                "question": question,
                "a": a,
                "b": b,
                "c": c,
                "d": d,
                "answer": answer
            })
            save_quizzes(quizzes)
            await update.message.reply_text("✅ Question added!")
        except Exception as e:
            await update.message.reply_text("⚠ Error adding question. Please follow correct format.")
        return

    # Quiz answering
    if "quizzes" not in context.user_data:
        return

    index = context.user_data["index"]
    quizzes = context.user_data["quizzes"]

    if index >= len(quizzes):
        return

    correct = quizzes[index].get("answer", "").lower()
    if text.strip().lower() == correct.lower():
        context.user_data["score"] += 1
        await update.message.reply_text("✅ Correct!")
    else:
        await update.message.reply_text(f"❌ Wrong. Correct: {correct.upper()}")

    context.user_data["index"] += 1
    await send_question(update, context)

# Leaderboard
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = load_scores()
    if not scores:
        await update.message.reply_text("🚫 No scores yet.")
        return

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    result = "\n".join([f"{name}: {score}" for name, score in sorted_scores])
    await update.message.reply_text("🏆 Leaderboard:\n" + result)

# Run bot
if _name_ == "_main_":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    print("✅ Bot is starting... Please wait")
    app.run_polling()
