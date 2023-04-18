/* jshint unused:vars */
'use strict';

angular.module('suporte.controllers', [
	'dlg.confirm.controller',
	'activities.controller',
	'add-activity.controller',
	'timeline.controller',
	'edit-activity.controller'
])

	.controller('MainCtrl', ['$scope', '$state', '$window', '$location', 'AuthService', 'AUTH_EVENTS', 'PROXIMIDADE_SUPORTE_URLS',
		'Notify',
		function ($scope, $state, $window, $location, AuthService, AUTH_EVENTS, PROXIMIDADE_SUPORTE_URLS, Notify) {

			$scope.profilePopover = { template: "profileTemplate.html", user: null, isOpen: false };
			$scope.appsPopover = { template: "appsTemplate.html", apps: [], isOpen: false, show_apps: false };
			$scope.disable = { controls: false };

			$scope.lt = { activities: {}, config: {}, org: null };

			$scope.appUrl = $location.absUrl();

			$scope.$on(AUTH_EVENTS.Authenticated, function () {
				AuthService.GetUser().then(function (user) {
					$scope.profilePopover.user = user;
					$scope.appsPopover.apps = angular.copy(user.apps);
					$scope.appsPopover.show_apps = !_.isEmpty(_.filter(user.apps, app => app.id != 'suporte-prox'));
					$scope.lt.org = user.organization;
				});
			});

			$scope.UserData = function () {
				AuthService.GetUser().then(function (user) {
					$scope.profilePopover.user = user;
				});
			};

			$scope.profile = function () {
				$scope.profilePopover.isOpen = false;
				$window.open(PROXIMIDADE_SUPORTE_URLS.profile_url, '_self');
			};

			$scope.administrate = function () {
				$scope.profilePopover.isOpen = false;
				$window.open(PROXIMIDADE_SUPORTE_URLS.admin, '_self');
			};

			$scope.logout = function () {
				AuthService.Logout().then(function (result) {
					$scope.profilePopover.isOpen = false;
					$scope.appsPopover.isOpen = false;
					$window.open(PROXIMIDADE_SUPORTE_URLS.unauthenticated, '_self');
					$scope.ShowNotify({
						texto: "Desconectado com sucesso.",
						titulo: "Logout",
						tipo: 'info',
						position: 'right',
						duration: 3000,
						container: angular.element(document.querySelector("#id_notify"))
					});
				}, function (error) {
					$window.open(PROXIMIDADE_SUPORTE_URLS.unauthenticated, '_self');
				});
			};

			$scope.ShowNotify = function (opt) {
				Notify.notify(opt);
			};

			$scope.mainloading = false;
			$scope.goto_main = function () {
				if ($state.current.name != 'main')
					$scope.mainloading = true;
				$state.go('main');
			};

		}])

	.filter('date_filter', ['$parse', '$filter', function ($parse, $filter) {
		return function (collection, properties, search, format) {

			function toArray(object) {
				return angular.isArray(object) ? object : Object.keys(object).map(function (key) {
					return object[key];
				});
			}
			var comparator;

			search = (angular.isString(search) || angular.isNumber(search)) ?
				String(search).toLowerCase() : undefined;

			collection = angular.isObject(collection) ? toArray(collection) : collection;

			if (!angular.isArray(collection) || angular.isUndefined(search)) {
				return collection;
			}

			return collection.filter(function (elm) {
				return properties.some(function (prop) {
					comparator = $parse(prop)(elm);

					if (angular.isDate(comparator)) {
						comparator = $filter('date')(comparator, format).toLowerCase();
					}
					else if (angular.isString(comparator) || angular.isNumber(comparator)) {
						comparator = String(comparator).toLowerCase();
					}
					else {
						return false;
					}
					return comparator.contains(search);
				});
			});
		};
	}])

	.filter('parseArray', [function () {
		return function (input) {
			if (!input)
				return input;

			if (_.isArray(input))
				return _.toString(input).replace(",", "; ");
			else
				return input;
		};
	}])

	.filter('capitalize', [function () {
		return function (s) {
			return (angular.isString(s) && s.length > 0) ? s[0].toUpperCase() + s.substr(1).toLowerCase() : s;
		}
	}]);
