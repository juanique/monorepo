export enum NameStyle {
    Simple,
    Fancy
}

export function formatNamePretty(name: string, style: NameStyle): string {
    switch (style) {
        case NameStyle.Simple:
            return name.toUpperCase();
        case NameStyle.Fancy:
            return `✨ ${name} ✨`;
        default:
            return name;
    }
}
