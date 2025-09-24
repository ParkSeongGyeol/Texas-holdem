const PokerGame = require('../src/game');
const Card = require('../src/card');
const Deck = require('../src/deck');

console.log('Running tests...\n');

// Test Card class
console.log('Testing Card class:');
const card = new Card('♠', 'A');
console.log(`Card: ${card.toString()}, Value: ${card.getValue()}`);

// Test Deck class
console.log('\nTesting Deck class:');
const deck = new Deck();
console.log(`Deck has ${deck.cards.length} cards`);
const dealtCard = deck.deal();
console.log(`Dealt card: ${dealtCard.toString()}`);

// Test basic game setup
console.log('\nTesting Game setup:');
const game = new PokerGame();
game.addPlayer('Alice', 1000);
game.addPlayer('Bob', 1000);

console.log('Players added successfully');
console.log('Running basic game simulation...\n');

game.start();