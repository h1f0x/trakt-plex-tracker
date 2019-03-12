// Code goes here

var app = angular.module("app");

app.filter('offset', function () {
    return function (input, start) {
        start = parseInt(start, 10);
        return input.slice(start);
    };
});


app.controller("tvTraker", function ($scope, $http) {
    setTimeout(function () {
        $scope.$apply(function () {
            $http.get('data/shows.json').then(function (data) {

                data_headers = data.headers();

                $scope.lastUpdate = data_headers['last-modified'];
                $scope.data = data.data;
                $scope.upcoming = [];

                current_date = Math.floor(Date.now() / 1000)

                angular.forEach(data.data, function (show, key) {
                    angular.forEach(show.seasons, function (season, key_season) {
                        angular.forEach(season.episodes, function (episode, key_episode) {
                            if (episode.first_aired) {
                                if (episode.aired_timestamp > current_date) {
                                    if (episode.aired_timestamp < (current_date + 604800)) {
                                        episode.show = show.title
                                        episode.season = season.number
                                        $scope.upcoming.push(episode)
                                    }
                                }
                            }
                        })
                    })
                });
            });
        });
    }, 2000);
});