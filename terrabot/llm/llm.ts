import OpenAI from 'openai';

export class LLMClient {
    private client: OpenAI;

    constructor(apiKey: string) {
        this.client = new OpenAI({
            apiKey: apiKey
        });
    }

    /**
     * Sends a prompt to OpenAI and returns the response
     * @param prompt The text prompt to send to OpenAI
     * @returns The generated response text
     */
    async getCompletion(prompt: string): Promise<string> {
        try {
            const completion = await this.client.chat.completions.create({
                messages: [{ role: 'user', content: prompt }],
                model: 'gpt-3.5-turbo',
            });

            return completion.choices[0]?.message?.content || '';
        } catch (error) {
            console.error('Error getting completion:', error);
            throw error;
        }
    }
}
