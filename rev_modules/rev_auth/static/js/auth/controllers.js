
app.controller('UserMenuController', function($scope, UserService) {
	
	$scope.user = {
		'name' : 'Russell B'
	}
	
	function updateUserMenu() {
		$scope.isLoggedIn = UserService.isLoggedIn();
	}
	
	$scope.$on('userStateChanged', updateUserMenu);
});

app.controller('LoginFormController', function($scope, UserService) {
	$scope.doLogin = UserService.doLogin;
});

app.controller('LogoutController', function($scope, UserService) {
	UserService.doLogout();
});