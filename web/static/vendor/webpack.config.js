const webpack = require('webpack');

module.exports = {
    mode: 'production',
    entry: {
        notification: './components/index_notif.jsx',
    },
    output: {
        filename: '/static/js/react/[name].bundle.js'
    },
    devtool: 'inline-source-map',
    module: {
        rules: [

            // First Rule
            {
                test: /\.(jsx?)$/,
                exclude: /node_modules/,
                use: ['babel-loader']
            },

            // Second Rule
            {
                test: /\.css$/,
                use: [
                    {
                        loader: 'style-loader'
                    },
                    {
                        loader: 'css-loader',
                        options: {
                            modules: true,
                            localsConvention: 'camelCase',
                            sourceMap: true
                        }
                    }
                ]
            }
        ]
    },
};
