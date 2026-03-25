import {
	GameplayPresenter,
	GameplayView,
} from "../../src/presenters/GameplayPresenter";
import io from "socket.io-client";
import { GameStateDTO } from "../../../dtos/index";

// Mock the socket.io-client library to control its behavior in tests
jest.mock("socket.io-client", () => {
	const mockSocket = {
		on: jest.fn(),
		off: jest.fn(),
		emit: jest.fn(),
	};
	return jest.fn(() => mockSocket);
});

// Get a reference to the mocked socket instance
const mockedIO = io as jest.Mock;
const mockSocket = mockedIO();

describe("GameplayPresenter", () => {
	let presenter: GameplayPresenter;
	let mockView: GameplayView;
	const gameId = "test-game-123";
	const userId = "test-user-456";

	beforeEach(() => {
		// Clear all mocks before each test to ensure test isolation
		jest.clearAllMocks();
		jest.useFakeTimers();

		jest.spyOn(global, "setInterval");

		// Create a mock view object with jest functions
		mockView = {
			setGameState: jest.fn(),
			setPlayerCount: jest.fn(),
			setTimeLeft: jest.fn(),
			setUserId: jest.fn(),
			showAlert: jest.fn(),
		};

		// Mock document.cookie to provide a user session
		Object.defineProperty(document, "cookie", {
			writable: true,
			value: `user_session=${userId}`,
		});

		// Instantiate the presenter with the mock view and gameId
		presenter = new GameplayPresenter(mockView, gameId);
	});

	afterEach(() => {
		jest.useRealTimers();
	});

	it("should be created successfully", () => {
		expect(presenter).toBeDefined();
	});

	describe("initialization", () => {
		it("should set user id from cookie and emit join_room", () => {
			expect(mockView.setUserId).toHaveBeenCalledWith(userId);
			expect(mockSocket.emit).toHaveBeenCalledWith("join_room", {
				gameId,
				userId,
			});
		});

		it('should use "anon" as userId if cookie is not present', () => {
			Object.defineProperty(document, "cookie", {
				writable: true,
				value: "",
			});
			presenter = new GameplayPresenter(mockView, gameId);
			expect(mockView.setUserId).toHaveBeenCalledWith("anon");
			expect(mockSocket.emit).toHaveBeenCalledWith("join_room", {
				gameId,
				userId: "anon",
			});
		});

		it("should set up socket event listeners", () => {
			expect(mockSocket.on).toHaveBeenCalledWith(
				"room_update",
				expect.any(Function),
			);
			expect(mockSocket.on).toHaveBeenCalledWith(
				"game_state",
				expect.any(Function),
			);
			expect(mockSocket.on).toHaveBeenCalledWith(
				"game_started",
				expect.any(Function),
			);
			expect(mockSocket.on).toHaveBeenCalledWith("error", expect.any(Function));
		});

		it("should start a timer to update time left", () => {
			expect(setInterval).toHaveBeenCalledWith(expect.any(Function), 1000);
		});
	});

	describe("socket event handling", () => {
		let socketEventCallbacks: { [key: string]: (...args: any[]) => void } = {};

		beforeEach(() => {
			// Capture the callbacks passed to socket.on
			(mockSocket.on as jest.Mock).mockImplementation((event, callback) => {
				socketEventCallbacks[event] = callback;
			});
			// Re-initialize presenter to capture the new callbacks
			presenter = new GameplayPresenter(mockView, gameId);
		});

		it('should update player count on "room_update"', () => {
			socketEventCallbacks["room_update"]({ player_count: 5 });
			expect(mockView.setPlayerCount).toHaveBeenCalledWith(5);
		});

		it('should update game state and time on "game_state"', () => {
			const gameState = { time_remaining: 180 } as GameStateDTO;
			socketEventCallbacks["game_state"](gameState);
			expect(mockView.setGameState).toHaveBeenCalledWith(gameState);
			expect(mockView.setTimeLeft).toHaveBeenCalledWith(180);
		});

		it('should request an update on "game_started"', () => {
			socketEventCallbacks["game_started"]();
			expect(mockSocket.emit).toHaveBeenCalledWith("request_update", {
				gameId,
				userId,
			});
		});

		it('should show an alert on "error"', () => {
			socketEventCallbacks["error"]({ message: "A server error occurred." });
			expect(mockView.showAlert).toHaveBeenCalledWith(
				"A server error occurred.",
			);
		});
	});

	describe("user actions", () => {
		it('should emit "start_game_request" when handleStartGame is called', () => {
			presenter.handleStartGame();
			expect(mockSocket.emit).toHaveBeenCalledWith("start_game_request", {
				gameId,
				userId,
			});
		});

		it('should emit "send_message" with payload when handleSendMessage is called', () => {
			const messagePayload = { content: "Hello there!" };
			presenter.handleSendMessage(messagePayload);
			expect(mockSocket.emit).toHaveBeenCalledWith("send_message", {
				from_id: userId,
				gameId,
				content: "Hello there!",
			});
		});

		it('should emit "user_action" with payload when handleUserAction is called', () => {
			const action = "BUILD_DEV";
			const payload = { tile_id: "t1" };
			presenter.handleUserAction(action, payload);
			expect(mockSocket.emit).toHaveBeenCalledWith("user_action", {
				gameId,
				userId,
				action,
				payload,
			});
		});
	});

	describe("destroy", () => {
		it("should remove all socket listeners and clear the timer", () => {
			const clearIntervalSpy = jest.spyOn(global, "clearInterval");
			presenter.destroy();

			expect(mockSocket.off).toHaveBeenCalledWith("room_update");
			expect(mockSocket.off).toHaveBeenCalledWith("game_state");
			expect(mockSocket.off).toHaveBeenCalledWith("game_started");
			expect(mockSocket.off).toHaveBeenCalledWith("error");
			expect(clearIntervalSpy).toHaveBeenCalled();
		});
	});
});
