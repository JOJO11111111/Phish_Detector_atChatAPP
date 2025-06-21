package v1

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"realtime-chat-app/pkg/common/response"
	"realtime-chat-app/pkg/global/log"
	"strings"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// VoiceDetectionRequest represents the request body for voice detection
type VoiceDetectionRequest struct {
	AudioFileName string `json:"audio_file_name" binding:"required"`
}

// VoiceDetectionResponse represents the response from voice detection
type VoiceDetectionResponse struct {
	IsSynthetic bool    `json:"is_synthetic"`
	Confidence  float64 `json:"confidence"`
	Details     struct {
		RealScore      float64 `json:"real_score"`
		FakeScore      float64 `json:"fake_score"`
		MultiClassScores struct {
			GT            float64 `json:"gt"`
			Wavegrad      float64 `json:"wavegrad"`
			Diffwave      float64 `json:"diffwave"`
			ParallelWaveGan float64 `json:"parallel_wave_gan"`
			Wavernn       float64 `json:"wavernn"`
			Wavenet       float64 `json:"wavenet"`
			Melgan        float64 `json:"melgan"`
		} `json:"multi_class_scores"`
	} `json:"details"`
}

// DetectVoiceSynthetic handles the voice detection request
func DetectVoiceSynthetic(c *gin.Context) {
	var request VoiceDetectionRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		log.Logger.Error("Invalid request body", zap.Error(err))
		c.JSON(http.StatusBadRequest, response.FailMsg("Invalid request body"))
		return
	}

	// Validate audio file name
	if request.AudioFileName == "" {
		c.JSON(http.StatusBadRequest, response.FailMsg("Audio file name is required"))
		return
	}

	log.Logger.Info("Detecting voice for synthetic content", zap.String("audio_file", request.AudioFileName))

	// Call the Python voice detection service
	voiceResponse, err := callVoiceDetectionService(request.AudioFileName)
	if err != nil {
		log.Logger.Error("Failed to call voice detection service", zap.Error(err))
		c.JSON(http.StatusInternalServerError, response.FailMsg("Failed to analyze voice"))
		return
	}

	c.JSON(http.StatusOK, response.SuccessMsg("Voice analysis completed", voiceResponse))
}

// callVoiceDetectionService calls the Python voice detection service
func callVoiceDetectionService(audioFileName string) (*VoiceDetectionResponse, error) {
	// Construct the full path to the audio file
	// Assuming audio files are stored in the web/static/file/ directory
	audioFilePath := filepath.Join("web", "static", "file", audioFileName)
	
	// Check if the file exists
	if _, err := os.Stat(audioFilePath); os.IsNotExist(err) {
		return nil, fmt.Errorf("audio file not found: %s", audioFilePath)
	}

	// Prepare request to Python service
	requestBody := map[string]string{
		"audio_file_path": audioFilePath,
	}
	
	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Call the Python Flask service for voice detection
	resp, err := http.Post("http://localhost:5001/detect_voice", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to call Python voice detection service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("Python voice detection service returned status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var voiceResponse VoiceDetectionResponse
	if err := json.NewDecoder(resp.Body).Decode(&voiceResponse); err != nil {
		return nil, fmt.Errorf("failed to decode voice detection response: %w", err)
	}

	return &voiceResponse, nil
} 