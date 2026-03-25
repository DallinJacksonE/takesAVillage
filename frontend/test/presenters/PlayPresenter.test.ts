import { PlayPresenter, PlayView } from "../../src/presenters/PlayPresenter";
import { UserService } from "../../src/service/UserService";
import { ActiveGamesDTO, JoinableGameDTO } from "../../../dtos";

// Mock the UserService to control its behavior in tests
jest.mock("../../src/service/UserService");

const mockUserService = UserService as jest.MockedClass<typeof UserService>;

describe("PlayPresenter", () => {
	let presenter: PlayPresenter;
	let mockView: PlayView;

	beforeEach(() => {
		// Clear all mocks before each test to ensure test isolation
		jest.clearAllMocks();

		// Create a mock view object with jest functions
		mockView = {
			setJoinableGames: jest.fn(),
			setHasConsented: jest.fn(),
			navigateToGame: jest.fn(),
			showAlert: jest.fn(),
		};

		// Instantiate the presenter with the mock view
		presenter = new PlayPresenter(mockView);
	});

	it("should be created successfully", () => {
		expect(presenter).toBeDefined();
	});

	describe("handleConsent", () => {
		it("should show an alert if the user is not 18+", async () => {
			await presenter.handleConsent(false);
			expect(mockView.showAlert).toHaveBeenCalledWith(
				"You must be 18 or older to participate.",
			);
			expect(mockView.setHasConsented).not.toHaveBeenCalled();
		});

		it("should set consent and start fetching games if user is 18+ and server agrees", async () => {
			// Arrange: Mock the service to return a successful consent
			mockUserService.prototype.consent.mockResolvedValue({
				message: "Consent accepted",
				userId: "user-123",
			});
			// Spy on startFetchingGames to ensure it's called without executing its timers
			jest.spyOn(presenter, "startFetchingGames").mockImplementation(() => {});

			// Act
			await presenter.handleConsent(true);

			// Assert
			expect(mockUserService.prototype.consent).toHaveBeenCalled();
			expect(mockView.setHasConsented).toHaveBeenCalledWith(true);
			expect(presenter.startFetchingGames).toHaveBeenCalled();
			expect(mockView.showAlert).not.toHaveBeenCalled();
		});

		it("should show an alert if the server rejects the consent request", async () => {
			mockUserService.prototype.consent.mockResolvedValue(null);
			await presenter.handleConsent(true);
			expect(mockView.showAlert).toHaveBeenCalledWith(
				"Server rejected consent request",
			);
			expect(mockView.setHasConsented).not.toHaveBeenCalled();
		});
	});

	describe("game fetching", () => {
		beforeEach(() => {
			jest.useFakeTimers();
			mockUserService.prototype.getActiveGames.mockResolvedValue({
				games: [],
			});
		});

		afterEach(() => {
			jest.useRealTimers();
		});

		it("startFetchingGames should call fetchGames immediately and then every 10 seconds", () => {
			const fetchGamesSpy = jest
				.spyOn(presenter as any, "fetchGames")
				.mockImplementation(() => {});
			presenter.startFetchingGames();

			expect(fetchGamesSpy).toHaveBeenCalledTimes(1);

			jest.advanceTimersByTime(10000);
			expect(fetchGamesSpy).toHaveBeenCalledTimes(2);

			jest.advanceTimersByTime(20000);
			expect(fetchGamesSpy).toHaveBeenCalledTimes(4);

			presenter.stopFetchingGames();
			fetchGamesSpy.mockRestore();
		});

		it("stopFetchingGames should clear the interval for fetching games", () => {
			const clearIntervalSpy = jest.spyOn(global, "clearInterval");
			presenter.startFetchingGames();
			presenter.stopFetchingGames();
			expect(clearIntervalSpy).toHaveBeenCalled();
		});

		it("fetchGames should call the user service and update the view with games", async () => {
			const games: ActiveGamesDTO = {
				games: [{ id: "1", name: "Game 1", players: "1/10" }],
			};
			mockUserService.prototype.getActiveGames.mockResolvedValue(games);

			await (presenter as any).fetchGames();

			expect(mockUserService.prototype.getActiveGames).toHaveBeenCalled();
			expect(mockView.setJoinableGames).toHaveBeenCalledWith(games.games);
		});
	});

	describe("startNewGame", () => {
		it("should navigate to a new game when creation is successful", async () => {
			const newGame = { gameId: "new-game-123" };
			mockUserService.prototype.newGame.mockResolvedValue(newGame);

			await presenter.startNewGame();

			expect(mockUserService.prototype.newGame).toHaveBeenCalled();
			expect(mockView.navigateToGame).toHaveBeenCalledWith("new-game-123");
		});
	});

	describe("joinGame", () => {
		it("should navigate to the game when joining is successful", async () => {
			const gameId = "existing-game-456";
			const joinedGame = { gameId: gameId };
			mockUserService.prototype.joinGame.mockResolvedValue(joinedGame);

			await presenter.joinGame(gameId);

			expect(mockUserService.prototype.joinGame).toHaveBeenCalledWith(gameId);
			expect(mockView.navigateToGame).toHaveBeenCalledWith(gameId);
		});
	});
});
