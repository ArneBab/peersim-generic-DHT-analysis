challengerApp.filter('toLocale', function () {
  return function (item) {
    return new Date(item).toLocaleString()
  }
}).filter('prettyName', function () {
  return function (item) {
    if (item.replace)
      return item.replace(/_/g, ' ')
    return item
  }
})
