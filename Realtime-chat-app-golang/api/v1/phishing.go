package v1

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"realtime-chat-app/pkg/common/response"
	"realtime-chat-app/pkg/global/log"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

// PhishScanRequest represents the request body for URL scanning
type PhishScanRequest struct {
	URL string `json:"url" binding:"required"`
}

// PhishScanResponse represents the response from phishing detection
type PhishScanResponse struct {
	IsPhishing bool    `json:"is_phishing"`
	Confidence float64 `json:"confidence"`
	Details    struct {
		URL              string  `json:"url"`
		ImagePhishScore  float64 `json:"image_phish_score"`
		ImageDecision    int     `json:"image_decision"`
		TextPhishScore   float64 `json:"text_phish_score"`
		TextDecision     int     `json:"text_decision"`
		ImageVector      string  `json:"image_vector"`
		TextVector       string  `json:"text_vector"`
		FusedFeatures    string  `json:"fused_features"`
	} `json:"details"`
}

// ScanURLForPhishing handles the phishing detection request
func ScanURLForPhishing(c *gin.Context) {
	var request PhishScanRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		log.Logger.Error("Invalid request body", zap.Error(err))
		c.JSON(http.StatusBadRequest, response.FailMsg("Invalid request body"))
		return
	}

	// Validate URL
	if request.URL == "" {
		c.JSON(http.StatusBadRequest, response.FailMsg("URL is required"))
		return
	}

	log.Logger.Info("Scanning URL for phishing", zap.String("url", request.URL))

	// Call the Python phishing detection service
	phishResponse, err := callPhishingDetectionService(request.URL)
	if err != nil {
		log.Logger.Error("Failed to call phishing detection service", zap.Error(err))
		c.JSON(http.StatusInternalServerError, response.FailMsg("Failed to scan URL"))
		return
	}

	c.JSON(http.StatusOK, response.SuccessMsg("Scan completed", phishResponse))
}

// callPhishingDetectionService calls the Python Flask service for phishing detection
func callPhishingDetectionService(url string) (*PhishScanResponse, error) {
	// Prepare request to Python service
	requestBody := map[string]string{
		"url": url,
	}
	
	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Call the Python Flask service (assuming it runs on port 5000)
	resp, err := http.Post("http://localhost:5000/scan", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to call Python service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("Python service returned status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var phishResponse PhishScanResponse
	if err := json.NewDecoder(resp.Body).Decode(&phishResponse); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &phishResponse, nil
} 