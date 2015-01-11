
app.service('UserService', function($rootScope) {
	
	var _isLoggedIn = false;
	
	this.isLoggedIn = function() {
		return _isLoggedIn;
	}
	
	this.doLogin = function() {
		_isLoggedIn = true;
		$rootScope.$broadcast('userStateChanged');
	};

	this.doLogout = function() {
		_isLoggedIn = false;
		$rootScope.$broadcast('userStateChanged');
	};
});