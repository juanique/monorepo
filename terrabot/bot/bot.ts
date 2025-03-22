import { Telegraf } from 'telegraf';
import { message } from 'telegraf/filters';
import { LLMClient } from '../llm/llm';

export class Terrabot {
    private bot: Telegraf;
    private llm?: LLMClient;

    constructor(telegramApiKey: string, llm?: LLMClient) {
        this.bot = new Telegraf(telegramApiKey);
        this.llm = llm;
        this.setupHandlers();
    }

    private setupHandlers() {
        // Handle text messages
        this.bot.on(message('text'), async (ctx) => {
            console.log('Received text:', ctx.message.text);
            
            if (ctx.message.text.toLowerCase() === '@walk_the_terrabot tell me a joke') {
                if (this.llm) {
                    try {
                        const joke = await this.llm.getCompletion('Tell me a short, funny joke');
                        await ctx.reply(joke);
                    } catch (error) {
                        console.error('Error getting joke:', error);
                        await ctx.reply('Sorry, I had trouble thinking of a joke right now 😅');
                    }
                } else {
                    await ctx.reply('Sorry, I don\'t know any jokes yet! My joke module isn\'t configured 😅');
                }
                return;
            }
        });

        // Handle stickers
        this.bot.on(message('sticker'), (ctx) => {
            console.log('Received sticker:', ctx.message.sticker.emoji);
        });

        // Handle channel posts
        this.bot.on('channel_post', (ctx) => {
            if ('text' in ctx.channelPost) {
                ctx.reply(`Channel post received: ${ctx.channelPost.text}`);
            }
        });

        // Catch-all middleware
        this.bot.use((ctx, next) => {
            console.log('Received an update:', ctx.updateType, ctx.update);
            return next(); // Pass control to the next middleware/handler
        });
    }

    async start() {
        try {
            const botInfo = await this.bot.telegram.getMe();
            console.log('Bot started:', botInfo);
            await this.bot.launch();

            // Enable graceful stop
            process.once('SIGINT', () => this.bot.stop('SIGINT'));
            process.once('SIGTERM', () => this.bot.stop('SIGTERM'));
        } catch (error) {
            console.error('Failed to start bot:', error);
            throw error;
        }
    }
}
