/* global __dirname, require, process */

const gulp = require('gulp');
const log = require('fancy-log');
const colors = require('ansi-colors');
const gulpif = require('gulp-if');
const less = require('gulp-less');
const cleanCSS = require('gulp-clean-css');
const uglify = require('gulp-uglify');
const sourcemaps = require('gulp-sourcemaps');
const argv = require('yargs').argv;
const browserSync = require('browser-sync');
const del = require('del');

const handleError = task => {
    return err => {
        log.warn(colors.bold(colors.red(`[ERROR] ${task}:`)), colors.red(err));
    };
}
const buildDir = 'static_build';
// gulp build --production
const production = !!argv.production;

/**
 * Delete the static_build directory and start fresh.
 */
gulp.task('clean', () => {
    return del([buildDir]);
});;

/**
 * Copy assets from various sources into the static_build dir for processing.
 */
gulp.task('assets', () => {
    return gulp.src(['static/**/*']).pipe(gulp.dest(buildDir));
});

/**
 * Find all LESS files from bundles in the static_build directory and compile them.
 */
gulp.task('less', ['assets'], () => {
    return gulp.src(`${buildDir}/less/*.less`)
        .pipe(gulpif(!production, sourcemaps.init()))
        .pipe(less().on('error', handleError('LESS')))
        // we don't serve the source files
        // so include scss content inside the sourcemaps
        .pipe(gulpif(!production, sourcemaps.write()))
        .pipe(gulp.dest(buildDir + '/css'));
});

/**
 * Minify all of the CSS files after compilation.
 */
gulp.task('css:minify', ['less'], () => {
    return gulp.src(`${buildDir}/css/**/*.css`, {base: buildDir})
        .pipe(cleanCSS().on('error', handleError('CLEANCSS')))
        .pipe(gulp.dest(buildDir));
});

/**
 * Minify all of the JS files after compilation.
 */
gulp.task('js:minify', ['assets'], () => {
    return gulp.src(`${buildDir}/js/**/*.js`, {base: buildDir})
        .pipe(uglify().on('error', handleError('UGLIFY')))
        .pipe(gulp.dest(buildDir));
});

/**
 * Start the browser-sync daemon for local development.
 */
gulp.task('browser-sync', ['assets', 'less'], () => {
    const proxyURL = process.env.BS_PROXY_URL || 'localhost:8000';
    const openBrowser = !(process.env.BS_OPEN_BROWSER === 'false');
    browserSync({
        proxy: proxyURL,
        open: openBrowser,
        serveStatic: [{
            route: '/static',
            dir: buildDir
        }]
    });
});

/**
 * Reload tasks used by `gulp watch`.
 */
gulp.task('reload-other', ['assets'], browserSync.reload);
gulp.task('reload-less', ['less'], browserSync.reload);
gulp.task('reload', browserSync.reload);

// --------------------------
// DEV/WATCH TASK
// --------------------------
gulp.task('watch', ['browser-sync'], () => {
    gulp.watch([
        'static/**/*',
        '!static/less/**/*',
    ], ['reload-other']);

    // --------------------------
    // watch:css, less, and sass
    // --------------------------
    gulp.watch('static/less/**/*', ['reload-less']);

    // --------------------------
    // watch:html
    // --------------------------
    gulp.watch('standup/**/*.html', ['reload']);

    log.info(colors.bggreen('Watching for changes...'));
});

/**
 * Build all assets in prep for production.
 * Pass the `--production` flag to turn off sourcemaps.
 */
gulp.task('build', ['js:minify', 'css:minify']);

gulp.task('default', ['watch']);
