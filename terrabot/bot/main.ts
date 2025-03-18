import { Terrabot } from 'terrabot/bot/bot';

function getApiKey(): string {
    const apiKey = process.argv[2];
    if (!apiKey) {
        console.error('Please provide the Telegram API key as a command line argument');
        process.exit(1);
    }
    return apiKey;
}

async function main() {
    try {
        const apiKey = getApiKey();
        const bot = new Terrabot(apiKey);
        await bot.start();
    } catch (error) {
        console.error('Bot initialization failed:', error);
        process.exit(1);
    }
}

main();
