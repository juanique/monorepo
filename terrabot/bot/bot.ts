import { Telegraf } from 'telegraf';

export class Terrabot {
    private bot: Telegraf;

    constructor(apiKey: string) {
        this.bot = new Telegraf(apiKey);
        this.setupHandlers();
    }

    private setupHandlers() {
        this.bot.on('message', (ctx) => {
            if (ctx.message.text) {
                console.log('Received message:', ctx.message.text);
            }
            ctx.reply('Hello!');
        });

        this.bot.on('sticker', (ctx) => {
            console.log('Received sticker:', ctx.message.sticker.emoji);
        });

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
