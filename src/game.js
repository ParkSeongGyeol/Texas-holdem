const Deck = require('./deck');
const Player = require('./player');

class PokerGame {
    constructor() {
        this.deck = new Deck();
        this.players = [];
        this.communityCards = [];
        this.pot = 0;
        this.currentRound = 'preflop';
        this.dealerPosition = 0;
    }

    addPlayer(name, chips = 1000) {
        this.players.push(new Player(name, chips));
    }

    start() {
        if (this.players.length < 2) {
            console.log('Need at least 2 players to start the game');
            return;
        }

        console.log('Starting new hand...');
        this.newHand();
    }

    newHand() {
        this.deck.reset();
        this.deck.shuffle();
        this.communityCards = [];
        this.pot = 0;
        this.currentRound = 'preflop';

        this.players.forEach(player => player.reset());

        this.dealHoleCards();
        this.displayGameState();
    }

    dealHoleCards() {
        for (let i = 0; i < 2; i++) {
            this.players.forEach(player => {
                if (player.isActive) {
                    player.receiveCard(this.deck.deal());
                }
            });
        }
    }

    dealFlop() {
        this.deck.deal(); // Burn card
        for (let i = 0; i < 3; i++) {
            this.communityCards.push(this.deck.deal());
        }
        this.currentRound = 'flop';
    }

    dealTurn() {
        this.deck.deal(); // Burn card
        this.communityCards.push(this.deck.deal());
        this.currentRound = 'turn';
    }

    dealRiver() {
        this.deck.deal(); // Burn card
        this.communityCards.push(this.deck.deal());
        this.currentRound = 'river';
    }

    displayGameState() {
        console.log('\n--- Game State ---');
        console.log(`Round: ${this.currentRound}`);
        console.log(`Pot: ${this.pot}`);
        console.log(`Community Cards: ${this.communityCards.map(card => card.toString()).join(' ')}`);

        console.log('\nPlayers:');
        this.players.forEach(player => {
            console.log(player.toString());
        });
        console.log('------------------\n');
    }
}

module.exports = PokerGame;