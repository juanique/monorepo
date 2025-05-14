import { formatNamePretty, NameStyle } from './formatting/formatting';

function main() {
    const name = "John Doe";
    const formattedName = formatNamePretty(name, NameStyle.Fancy);
    console.log(`Formatted Name: ${formattedName}`);
}

main();
