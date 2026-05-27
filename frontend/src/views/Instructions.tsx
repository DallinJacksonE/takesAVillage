import React from "react";

const Instructions: React.FC = () => {
  return (
    <div className='card'>
      <h1 style={{ marginBottom: "1rem" }}>How to Play: Takes a Village</h1>
      <p className='intro'>
        Welcome to the Village. You are spawning in an undeveloped area with raw
        resources. Your goal is to survive, build developments, and
        manage your social reputation. Teamwork is key, you will find yourself
        unable to survive alone.
      </p>

      <div style={{ marginTop: "2rem" }}>
        <h3>The Daily Cycle</h3>
        <p>Each day is split into three phases:</p>

        <div
          style={{
            paddingLeft: "20px",
            borderLeft: "3px solid #333",
            margin: "20px 0",
          }}
        >
          <h4>1. Work Phase</h4>
          <p>
            You can choose to produce resources at your developments, build a development,
            or contest the ownership of another player's development. In the beginning, you
            start with no workable land, you must build, trade, and work to survive. If you
            own a development, you can employ other players to work for you. Resources all
            go to the owner, so trust that they will fulfill promises by paying you back
            in the trade phase is vital. Contesting ownership will do nothing on the turn of
            initiation, but the following day players will be unable to work at a contested
            development, be aware that this takes your action, and you will be unable to work
            normal jobs if you chose to contest or defend. At the end of the day, if the attackers
            have more people supporting, the development falls into the hands of the initiator, whereas
            if the defenders win, the development stays with the owner. In the event of a tie the development
            remains under contest the following day. For either the owner or initial contester to win, they must
            participate in the contest, or the other respective party wins regardless of supporter count.
          </p>

          <h4>2. Trade Phase</h4>
          <p>
            Trade your resources with others. Players can "cheat" in trades by promising
            one thing but delivering another, or nothing at all. Honest trade builds trust;
            swindling builds wealth but hurts reputation. Contact between players allows for
            some trades to be dependent upon other actions later. For example, one player might
            offer another 1 food and iron in exchange for helping contest a development the
            following day, or sharing fire for the next 2 days.
          </p>

          <h4>3. Night Phase</h4>
          <p>
            Every night players must find warmth and eat food or risk rising sickness chances,
            upon both eating and being warm players sickness chance will fall, or a sick player
            will start to recover. Upon getting sick a second time while already in a sick state,
            players die and their property can be stolen by a contest action much easier than before.
            to get warm players have the option to start fires by spending wood, and inviting other players
            to sit with them. The fire hosts have the power to turn away or invite whoever they please.
            Food is always consumed from the player's own inventory automatically.
          </p>
        </div>

        <h3>Survival Mechanics</h3>
        <ul style={{ lineHeight: "1.6" }}>
          <li>
            <strong>Food:</strong> You must consume 1 Food every day. Upon not eating your sickness
            chance will rise strongly. In default games this is 20%.
          </li>
          <li>
            <strong>Wood:</strong> You must sit at a fire every day, which costs 1 to start. If you
            fail to find warmth, your chance of sickness increases as well. The default rate is 10%.
          </li>
          <li>
            <strong>Sickness/Recovery:</strong> If you get sick, you cannot work, but you can still trade, after
            a sick day, if you both eat and find warmth, your sickness chance will fall, and your state will
            be recovering. Eat and find warmth again to return to healthy. This system means that for every time
            you get sick you lose 2 days' worth of actions at the very least. The default rate for sickness chance
            decrease is 7%
          </li>
        </ul>

        <h3>Winning</h3>
        <p>
          Peace looks like steady growth. War looks like slander and seizing developments. Use your resources
          and social standing to survive the longest and build the most prosperous village. Game length is at
          least 11 days, but will most likely be more, the random day length is to prevent behavior changes upon
          nearing game completion.
        </p>
      </div>
    </div>
  );
};

export default Instructions;
