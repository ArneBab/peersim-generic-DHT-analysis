challengerApp.filter('toLocale', function () {
    return function (item) {
        return new Date(item).toLocaleString()
    };
});
