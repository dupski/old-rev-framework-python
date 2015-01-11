
app.config(function($stateProvider) {

	$stateProvider
		.state('login', {
			url: "/login",
			templateUrl: "view/rev_auth/login"
		})
		.state('logout', {
			url: "/logout",
			templateUrl: "view/rev_auth/logout"
		});

});