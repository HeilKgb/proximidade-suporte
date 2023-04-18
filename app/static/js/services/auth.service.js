/* jshint unused:vars */
'use strict';

angular.module('auth.service', [])

.factory('AuthService', ['$http', '$q', '$cookies', 'Session',
  function ($http, $q, $cookies, Session) {

	var isAuthenticated =false;
	var CheckAuthenticated = function(){
		var deferred = $q.defer();
		if (isAuthenticated){
			deferred.resolve(Session.get_user());
		}
		else{
			$http.get('/auth/user/info').then(function(res){
				var data = res.data.data;
				if (!data.registered)
					deferred.reject({registered: false});
				else{
					var id = data.email;
					var session = Session.create(id, data);
					isAuthenticated = true;
					deferred.resolve(session.user);
				}
			}, function(error){
				isAuthenticated = false;
				deferred.reject(error);
			});
		}
		return deferred.promise;
	};

	var isAuthorized = function (roles){
		if (!angular.isArray(roles)) {
			roles = [roles];
		}
		return (!!Session.auth &&
			roles.indexOf(Session.auth.user.role) !== -1);
	};

	var GetUser = function (){
		var deferred = $q.defer();
		if (isAuthenticated){
			deferred.resolve(Session.get_user());
		}
		else{
			$http.get('/auth/user/info').then(function(res){
				var data = res.data.data;
				var id = data.email;
				var session = Session.create(id, data);
				isAuthenticated = true;
				deferred.resolve(session.user);
			}, function(error){
				isAuthenticated = false;
				deferred.reject(error);
			});
		}
		return deferred.promise;
	};

	var Logout = function (){
		var deferred = $q.defer();
		var xsrfcookie = $cookies.get('_xsrf');
		var req = {
			method: 'POST',
			url: '/auth/logout',
			data: {},
			headers: { 'Content-Type': 'application/json', 'X-XSRFToken' : xsrfcookie},
			config: {}
		};
		$http(req)
		.then(function(response){
			Session.destroy(true);
			deferred.resolve(Session.auth === null);
		}, function(error){
			Session.destroy(true);
			deferred.reject(error);
		});
		return deferred.promise;
	};

	var authService = {
		CheckAuthenticated: CheckAuthenticated,
		isAuthorized: isAuthorized,
		GetUser: GetUser,
		Logout: Logout
	};
	return authService;
}])

.service('Session', ['$localStorage', '$cookies', 'APP_CONSTANTS', 'PROX_SUPORTE_URLS',
  function ($localStorage, $cookies, APP_CONSTANTS, PROX_SUPORTE_URLS) {

	this.auth = $localStorage.session;

	var version = 1.0;

	var set_user = function(data){
		var auth_user = {
			email: data.email,
			fullname: data.fullname,
			organization: data.organization,
			mobile: data.mobile,
			device_token: data.device_token,
			method: data.method,
			registered: data.registered,
			has_questions: data.has_questions,
			info: data.info,
			role: data.role,
			avatar: data.avatar,
			apps : data.apps,
			current_sign_in_at: data.current_sign_in_at,
			current_sign_in_ip: data.current_sign_in_ip,
			created_at: data.created_at,
			updated_at: data.updated_at,
			version: version
		};
		return auth_user;
	};

	this.get_user = function(){
		if (this.auth && this.auth.user)
			return (this.auth.user);
		else
			return null;
	};

	this.has_user = function(){
		return (this.auth && this.auth.user && this.auth.user.registered);
	};

	this.create = function (sessionId, user) {
		var session = {id: sessionId, user: set_user(user)};
		$localStorage.session = session;
		this.auth = session;
		return {user: session.user};
	};

	this.destroy = function (all) {
		all = (typeof all !== 'undefined') ? all : false;
		delete $localStorage.session;
		delete this.auth;
		if (all){
			$cookies.remove(APP_CONSTANTS.token);
			$cookies.remove('VAT',{'domain': PROX_SUPORTE_URLS.domain});
		}
		return this.auth;
	};

	var token = $cookies.get(APP_CONSTANTS.token);

	if(token === undefined){
		this.destroy(true);
	}

}]);
