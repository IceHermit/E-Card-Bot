# E-Card Discord Bot

> <i>The Slave has nothing. It is at the literal rock-bottom, and that is precisely why it can kill the Emperor.</i>

This is a discord bot based on the two-player turn-based (niche) card game <b>E-Card</b> from the anime <b>Kaiji: Ultimate Survivor</b>

## Rules of E-Card

- Two players play the game, one is the <b>Emperor</b> and the other is the <b>Slave.</b>
- Every player has 4 <b>Citizen</b> cards, and 1 card of their respective role (<b>Slave/Emperor</b>).
- There are 5 rounds, and each player chooses one card and exhausts it. There are 4 possibilities in each round: <br>
      i) Both players choose <b>Citizen.</b> The game proceeds to the next round. <br>
     ii) A <b>Slave</b> and an <b>Emperor</b> are played. The <b>Slave</b> kills the <b>Emperor</b> and the game ends.<br>
    iii) A <b>Slave</b> and a <b>Citizen</b> are played. The <b>Slave</b> can not do anything against the <b>Citizen,</b> but the <b>Slave</b> card is exhausted. <b>Emperor</b> wins. <br>
     iv) An <b>Emperor</b> and a <b>Citizen</b> are played. The <b>Citizen</b> can not do anything against the <b>Emperor,</b> but now the <b>Slave</b> can never kill <b>Emperor</b>. <b>Emperor</b> wins. <br> <br>

- The game is heavily favoured to the Emperor, so the Slave's winnings are amplified.

## Usage

- The `/register` command needs to be used for first time players. This creates an account of the player and gives them a starting bonus of 100 Debaloons, which they can bet in games of E-Card.
- Any registered player can call the `/play` command and set up a match against any other registered player. The two must agree to the side they are playing and the wagers.
- If any player goes out of Debaloons and goes bankrupt, they can use `/work` to get more money the good old (but slow) way.
- The balance of any registered player can be seen using the `/balance` command.

## Credits
This project was made by me <b>(IceHermit)</b> and my friend <b>(Rook-In-The-Rain).</b> <br>
Go check him out on <a href="https://github.com/Rook-In-The-Rain">GitHub.</a>
