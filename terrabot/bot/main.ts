import { Command } from 'commander';
import { Terrabot } from 'terrabot/bot/bot';
import { LLMClient } from 'terrabot/llm/llm';

const program = new Command();

program
    .name('terrabot')
    .description('A Telegram bot with optional LLM capabilities')
    .requiredOption('-t, --telegram-key <key>', 'Telegram Bot API Key')
    .option('-o, --openai-key <key>', 'OpenAI API Key')
    .parse(process.argv);

const options = program.opts();

async function main() {
    let llm: LLMClient | undefined;
    
    if (options.openaiKey) {
        llm = new LLMClient(options.openaiKey);
    }

    const bot = new Terrabot(options.telegramKey, llm);
    
    try {
        await bot.start();
        console.log('Bot started successfully!');
    } catch (error) {
        console.error('Failed to start bot:', error);
        process.exit(1);
    }
}

main(); 