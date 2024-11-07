import { formatNamePretty, NameStyle } from 'examples/ts/ts_library/formatting/formatting';

const name: string = "Ava";
const style: NameStyle = "fancy";

const formattedName = formatNamePretty(name, style);

console.log(`Formatted Name: ${formattedName}`);
