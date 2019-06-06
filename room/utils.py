import random 
import os

class BoggleGame:
    def __init__(self):
        self.deluxe_dice = [
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
        '''
        with open("words.txt") as f:
            self.words = [line.strip().lower() for line in f.readlines()]
        '''
        self.board = []
        # Build the 5x5 board
        for i in range(25):
            self.board.append(self.choose_deluxe_die())
        self.display_board = []
        for i in range(0, 25, 5):
            self.display_board.append(self.board[i:i+5])

    def check_word(self, word):
        options = []
        for i, c in enumerate(self.board):
            if (word != "" and (c.lower() == word[0] or 
                    (c.lower() == (word[0] + word[1]) and 
                     c.lower() == "qu"))):
                options.append(i)

        # Cycle through potentional beginnings
        valid = False
        for option in options:
            if self.check_word_helper(word, option, 0, []):
                valid = True
        return valid

    def bidx_is_valid(self, board_idx):
        return board_idx >= 0 and board_idx < 25

    def board_neighbors(self, board_idx):
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

    def check_word_helper(self, word, board_idx, word_idx, visited):
        if not self.bidx_is_valid(board_idx) or board_idx in visited:
            return False

        neighbors = self.board_neighbors(board_idx)
        word = word.lower()
        if word[word_idx] == self.board[board_idx].lower():
            visited.append(board_idx)
            if word_idx == len(word)-1:
                return word in self.words
            results = [self.check_word_helper(word, x, word_idx+1, visited) for x in neighbors]
            return True in results
        elif ((word_idx < len(word)-1) and 
                    (word[word_idx] + word[word_idx+1] == "qu" and 
                    self.board[board_idx].lower() == "qu")):
            if word_idx+1 == len(word)-1:
                return word in self.words
            results = [self.check_word_helper(word, x, word_idx+2, visited) for x in neighbors]
            return True in results
        return False

    def choose_deluxe_die(self):
        return random.choice(random.choice(self.deluxe_dice))

    def get_word_score(self, word):
        if len(word) > 7:
            return 11
        elif len(word) > 6:
            return 5
        elif len(word) > 5:
            return 3
        elif len(word) > 4:
            return 2
        return 1
