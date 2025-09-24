class Player {
    constructor(name, chips = 1000) {
        this.name = name;
        this.chips = chips;
        this.hand = [];
        this.currentBet = 0;
        this.isActive = true;
        this.hasFolded = false;
    }

    receiveCard(card) {
        this.hand.push(card);
    }

    bet(amount) {
        if (amount > this.chips) {
            amount = this.chips;
        }
        this.chips -= amount;
        this.currentBet += amount;
        return amount;
    }

    fold() {
        this.hasFolded = true;
        this.isActive = false;
    }

    reset() {
        this.hand = [];
        this.currentBet = 0;
        this.hasFolded = false;
        this.isActive = this.chips > 0;
    }

    toString() {
        return `${this.name} (${this.chips} chips): ${this.hand.map(card => card.toString()).join(', ')}`;
    }
}

module.exports = Player;