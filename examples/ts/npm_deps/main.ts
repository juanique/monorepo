import chalk from 'chalk';
import figlet from 'figlet';

const printFancyOutput = () => {
    console.log(chalk.blueBright.bold('Your Fancy Terminal Output!'));
    console.log(
        chalk.yellow(figlet.textSync('Hello, Juan!', { horizontalLayout: 'full' }))
    );

    console.log(
        chalk.greenBright.underline('Visit: ') + chalk.red.bold('www.example.com')
    );

    console.log(
        chalk.magentaBright(
            'Colors and styles can really make your terminal output pop!'
        )
    );
};

printFancyOutput();
