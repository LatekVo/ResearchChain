import curses
import requests
from langchain_core.output_parsers import StrOutputParser

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from core.lookup import web_lookup

colorama_init()

# llm = Ollama(model=MODEL_NAME) this is not necessary, but without this line the code does not work

output_parser = StrOutputParser()

chain = web_lookup | output_parser



def print_menu(stdscr, selected_row_idx, options):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Draw border
    stdscr.border()

    # Print title
    title = "Research Chain"
    stdscr.addstr(1, w // 2 - len(title) // 2, title)

    for idx, option in enumerate(options):
        x = w//2 - len(option)//2
        y = h//2 - len(options)//2 + idx
        if idx == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, option)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(y, x, option)
            stdscr.attroff(curses.color_pair(2))

    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)  # Hide cursor
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    stdscr.keypad(True)  # Enable keypad for non-character keys

    options = ["News", "Docs", "Wiki", "Exit"]
    selected_row_idx = 0

    print_menu(stdscr, selected_row_idx, options)

    while True:
        key = stdscr.getch()

        if key == curses.KEY_UP and selected_row_idx > 0:
            selected_row_idx -= 1
        elif key == curses.KEY_DOWN and selected_row_idx < len(options) - 1:
            selected_row_idx += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if selected_row_idx == len(options) - 1:
                exit()
            else:
                stdscr.clear()
                stdscr.border()
                stdscr.refresh()
                curses.endwin()  # End curses window
                print_menu(stdscr, selected_row_idx, options)
                return options[selected_row_idx]

        print_menu(stdscr, selected_row_idx, options)


    return options[selected_row_idx]

def print_input_field(stdscr, text_input):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Draw border
    stdscr.border()

    # Print title
    title = "Research Chain"
    stdscr.addstr(1, w // 2 - len(title) // 2, title)

    # Print text input field
    stdscr.addstr(h // 2, w // 2 - 20, "Enter Text:")
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(h // 2, w // 2 - 8, text_input)
    stdscr.attroff(curses.color_pair(1))


    stdscr.refresh()

def main2(stdscr):
    def get_input():
        text_input = ""
        print_input_field(stdscr, text_input)

        while True:
            key = stdscr.getch()

            if key == curses.KEY_ENTER or key in [10, 13]:
                break
            elif key == curses.KEY_BACKSPACE or key == 127:
                # Handle backspace to delete characters from the text input
                text_input = text_input[:-1]
            elif key >= 32 and key <= 126:
                # Add typed characters to the text input
                text_input += chr(key)

            print_input_field(stdscr, text_input)

        return text_input

    curses.curs_set(2)  # Show cursor
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    stdscr.keypad(True)  # Enable keypad for non-character keys

    text_input = get_input()
    curses.endwin()  # End curses window
    return text_input
try:
    mode_input = curses.wrapper(main)
    text_input = curses.wrapper(main2)
    print(f"{Fore.GREEN}{Style.BRIGHT}Mode:{Fore.RESET}{Style.RESET_ALL} {mode_input}", end="\n")
    print(f"{Fore.GREEN}{Style.BRIGHT}Input:{Fore.RESET}{Style.RESET_ALL} {text_input}", end="\n")
    chain_output = chain.invoke({"input": text_input, "mode": mode_input})
    print(f"{Fore.GREEN}{Style.BRIGHT}(llm){Fore.RESET}{Style.RESET_ALL} ", end="")
    print(chain_output, end="", flush=True)
    print(end='\n')
except requests.exceptions.ConnectionError:
    print(f"{Fore.RED}{Style.BRIGHT}Connection error, make sure Ollama server is running...{Fore.RESET}{Style.RESET_ALL}")
