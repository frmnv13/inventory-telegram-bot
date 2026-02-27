# /telegram-stock-bot/README.md

# Telegram Inventory Management Bot

A Telegram bot for managing a spare-part inventory using a MySQL database.

## Features

- **Free Text Search**: Simply type a keyword to search for products by name or code.
- **/list**: Get a paginated list of all products in the inventory.
- **/find `<keyword>`**: Explicitly search for a product.
- **/stock `<code>`**: Check the current stock level of a specific item.
- **/buy `<code>` `<quantity>`**: Simulate a purchase, which automatically deducts the item from the stock.
- **Safe Transactions**: The bot prevents stock from going into the negative and handles concurrent purchase requests safely.

## Prerequisites

- Python 3.8+
- MySQL Server
- A Telegram Bot Token

## Installation & Setup

1.  **Clone the Repository**

    ```bash
    git clone <your-repo-url>
    cd telegram-stock-bot
    ```

2.  **Create a Virtual Environment**

    It's highly recommended to use a virtual environment to manage dependencies.

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Setup**

    -   Make sure your MySQL server is running.
    -   Connect to your MySQL server and run the SQL script provided in the [Database Setup](#3-database-setup-mysql) section of the main guide to create the `inventory_bot` database, the `products` table, and insert sample data.

5.  **Configure the Bot**

    -   Open the `config.py` file.
    -   **`TELEGRAM_BOT_TOKEN`**: Get a token by talking to @BotFather on Telegram. Create a new bot and paste the token here.
    -   **`DB_CONFIG`**: Update the dictionary with your MySQL host, user, password, and the database name (`inventory_bot`).

    Example `config.py`:
    ```python
    TELEGRAM_BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'your_secret_password',
        'database': 'inventory_bot'
    }
    ```

## Running the Bot

Once everything is set up, run the main bot file:

```bash
python bot.py
