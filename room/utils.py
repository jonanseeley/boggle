from random import choice
import os

deluxe_dice = [
    ["A", "A", "A", "F", "R", "S"],
    ["A", "A", "E", "E", "E", "E"],
    ["A", "A", "F", "I", "R", "S"],
    ["A", "D", "E", "N", "N", "N"],
    ["A", "E", "E", "E", "E", "M"],
    ["A", "E", "E", "G", "M", "U"],
    ["A", "E", "G", "M", "N", "N"],
    ["A", "F", "I", "R", "S", "Y"],
    ["B", "J", "K", "Qu", "X", "Z"],
    ["C", "C", "N", "S", "T", "W"],
    ["C", "E", "I", "I", "L", "T"],
    ["C", "E", "I", "L", "P", "T"],
    ["C", "E", "I", "P", "S", "T"],
    ["D", "H", "H", "N", "O", "T"],
    ["D", "H", "H", "L", "O", "R"],
    ["D", "H", "L", "N", "O", "R"],
    ["D", "D", "L", "N", "O", "R"],
    ["E", "I", "I", "I", "T", "T"],
    ["E", "M", "O", "T", "T", "T"],
    ["E", "N", "S", "S", "S", "U"],
    ["F", "I", "P", "R", "S", "Y"],
    ["G", "O", "R", "R", "V", "W"],
    ["H", "I", "P", "R", "R", "Y"],
    ["N", "O", "O", "T", "U", "W"],
    ["O", "O", "O", "T", "T", "U"]
]


# TODO: Change so that we aren't loading all 170,000+ words for each user;
#   keep the words in the database or something
valid_words = []
with open("room/wordlist.txt", "r") as f:
    valid_words = [word.strip().lower() for word in f.readlines()]


def generate_board():
    board = []
    # Build the 5x5 board as a list of 25 random letters
    for i in range(25):
        board.append(choice(choice(deluxe_dice)))
    return board


def bidx_is_valid(board_idx):
    return board_idx >= 0 and board_idx < 25


def board_neighbors(board_idx):
    if board_idx % 5 == 0:
        if board_idx // 5 == 0:
            return [1, 5, 6]
        elif board_idx // 5 == 4:
            return [15, 16, 21]
        return [board_idx-5, board_idx+5, board_idx+1, board_idx-4, board_idx+6]
    elif board_idx % 5 == 4:
        if board_idx // 5 == 0:
            return [3, 8, 9]
        elif board_idx // 5 == 4:
            return [18, 19, 23]
        return [board_idx-5, board_idx+5, board_idx-1, board_idx-6, board_idx+4]
    else:
        return [board_idx-5, board_idx+5, board_idx-1, board_idx+1, board_idx-6, board_idx+6, board_idx-4, board_idx+4]


def check_word_helper(board, word, board_idx, word_idx, visited):
    if not bidx_is_valid(board_idx) or board_idx in visited:
        return False

    neighbors = board_neighbors(board_idx)
    word = word.lower()
    if word[word_idx] == board[board_idx].lower():
        visited.append(board_idx)
        if word_idx == len(word)-1:
            return word in valid_words
        results = [check_word_helper(board, word, x, word_idx+1, visited) for x in neighbors]
        return True in results
    elif ((word_idx < len(word)-1) and 
                (word[word_idx] + word[word_idx+1] == "qu" and 
                board[board_idx].lower() == "qu")):
        if word_idx+1 == len(word)-1:
            return word in valid_words
        results = [check_word_helper(board, word, x, word_idx+2, visited) for x in neighbors]
        return True in results
    return False


def check_word(board, word):
    # Don't accept words less than 4 letters long
    if len(word) < 4:
        return False
    options = []
    for i, c in enumerate(board):
        if (word != "" and (c.lower() == word[0] or 
                (c.lower() == (word[0] + word[1]) and 
                 c.lower() == "qu"))):
            options.append(i)

    # Cycle through potentional beginnings
    valid = False
    for option in options:
        if check_word_helper(board, word, option, 0, []):
            valid = True
    return valid


def get_word_score(word):
    if len(word) > 7:
        return 11
    elif len(word) > 6:
        return 5
    elif len(word) > 5:
        return 3
    elif len(word) > 4:
        return 2
    return 1
