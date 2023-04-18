'use strict';

angular.module('carousel.media.controller', [])

.controller('CarouselCtrl', ['$scope', '$sce', '$timeout', function($scope, $sce, $timeout) {

	$scope.title = 'Atividade: ' + $scope.$parent.activity.title;
	$scope.Close = function(){
		if(ElementPlaying)
			ElementPlaying.pause();
		$scope.$parent.views.option = 'main';
	};

	var ElementPlaying = null;
	$scope.active = 0;
	$scope.SetActive = function(media){
		$scope.views.option = 'carousel';
		if($scope.active != media.index || !ElementPlaying){
			$scope.active = media.index;
			if (ElementPlaying)
				ElementPlaying.pause();
			if(media.thumbnail.subtype != 'image'){
				var id = media.thumbnail.subtype + '_' + media.index;
				ElementPlaying = document.getElementById(id);
				ElementPlaying.play();
			}
		}
		$scope.selected_media = media;
	};

	$scope.childObj.SetActive = function (media){
		$scope.SetActive(media);
	};

	$scope.carousel = {
		active: 0, interval: 500000, view: true,
		noWrapSlides: false, no_transition : false,
	};

	$scope.CloseZoom = function(){
		$scope.$parent.views.option='carousel';
	};

	// The panzoom config model can be used to override default configuration values
	$scope.panzoom = {
		Config : {
			zoomLevels: 12, neutralZoomLevel: 5, scalePerZoomLevel: 1.5,
			initialPanX: 200, zoomOnDoubleClick: true, zoomToFitZoomLevelFactor: 1
		},
		Model: {},
		view: false
	};

	$scope.ShowZoom = function(url){
		$scope.views.option = 'panzoom';
		$scope.panzoom.Model.photo = url;
	};

}]);
