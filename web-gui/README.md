# Wazo IVR Web GUI

A modern React-based web interface for managing Wazo IVR System Plugin flows, TTS settings, and system configuration.

## Features

- **Dashboard**: System overview and status monitoring
- **Flow Management**: Create, edit, and deploy IVR flows with visual editor
- **TTS Management**: Test and configure text-to-speech settings
- **Settings**: System configuration and maintenance
- **Real-time Updates**: Live status monitoring and notifications

## Prerequisites

- Node.js 16+ and npm
- Wazo IVR System Plugin running on port 5000
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Installation

1. **Navigate to the web-gui directory**:
   ```bash
   cd web-gui
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm start
   ```

4. **Open your browser** and navigate to `http://localhost:3000`

## Building for Production

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Serve the built files**:
   ```bash
   # Using a simple HTTP server
   npx serve -s build -l 3000
   
   # Or using nginx/apache to serve the build directory
   ```

## Configuration

### Environment Variables

Create a `.env` file in the web-gui directory:

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:5000/api/ivr

# Optional: Enable debug mode
REACT_APP_DEBUG=true
```

### API Integration

The web GUI communicates with the Wazo IVR REST API. Ensure the API is running and accessible at the configured URL.

## Usage

### Dashboard

The dashboard provides an overview of:
- Total and active IVR flows
- TTS backend status
- Wazo service connectivity
- System health metrics

### Flow Management

1. **View Flows**: List all configured IVR flows
2. **Create Flow**: Use the visual editor to create new flows
3. **Edit Flow**: Modify existing flow configurations
4. **Deploy Flow**: Deploy flows to the Wazo system
5. **Delete Flow**: Remove unused flows

### TTS Management

1. **Test Voices**: Synthesize speech with different voices
2. **Configure Languages**: Set up multi-language support
3. **Voice Selection**: Choose appropriate voices for each language

### Settings

1. **System Configuration**: Modify plugin settings
2. **Wazo Integration**: Configure Wazo server connection
3. **Maintenance**: Clean up old files and cache

## Development

### Project Structure

```
web-gui/
├── public/                 # Static files
├── src/
│   ├── components/         # Reusable UI components
│   ├── pages/             # Page components
│   ├── services/          # API service layer
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Utility functions
│   ├── App.js             # Main app component
│   └── App.css            # Global styles
├── package.json           # Dependencies and scripts
└── README.md             # This file
```

### Available Scripts

- `npm start`: Start development server
- `npm run build`: Build for production
- `npm test`: Run tests
- `npm run eject`: Eject from Create React App

### Adding New Features

1. **Create components** in `src/components/`
2. **Add pages** in `src/pages/`
3. **Extend API services** in `src/services/api.js`
4. **Add custom hooks** in `src/hooks/`

### Styling

The project uses Tailwind CSS for styling. Key classes:
- `btn-primary`: Primary action buttons
- `btn-secondary`: Secondary action buttons
- `form-input`: Form input fields
- `card`: Card containers
- `status-*`: Status indicators

## Troubleshooting

### Common Issues

1. **API Connection Failed**:
   - Check if the Wazo IVR API is running
   - Verify the API URL in environment variables
   - Check network connectivity

2. **Build Errors**:
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility

3. **TTS Not Working**:
   - Verify TTS backend configuration
   - Check browser audio permissions
   - Test with different voices

### Debug Mode

Enable debug mode by setting `REACT_APP_DEBUG=true` in your environment variables.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the main project LICENSE file for details.
