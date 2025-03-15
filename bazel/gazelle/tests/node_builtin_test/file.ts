import fs from 'fs';
import path from 'path';

export function readFile(filePath: string): string {
    return fs.readFileSync(path.resolve(filePath), 'utf8');
}
